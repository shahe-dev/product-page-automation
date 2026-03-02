"""
Google Sheets Manager Service for PDP Automation v.3

Handles:
- Template sheet copying and creation
- Content population with batch updates
- Field mapping for 6 template types
- Read-back validation
- Permission management
- Rate limiting and retry logic
- Shared Drive integration
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials

from app.config.settings import get_settings
from app.models.enums import TemplateType
from app.services.template_fields import get_cell_mapping

logger = logging.getLogger(__name__)


# Data Classes
@dataclass
class SheetResult:
    """Result of sheet creation operation."""
    sheet_id: str
    sheet_url: str
    title: str
    template_type: str
    created_at: str


@dataclass
class PopulateResult:
    """Result of sheet population operation."""
    sheet_id: str
    total_fields: int
    fields_written: int
    fields_failed: int
    failures: list[dict] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of read-back validation."""
    sheet_id: str
    total_checked: int
    matches: int
    mismatches: int
    details: list[dict] = field(default_factory=list)


# Custom Exceptions
class SheetsManagerError(Exception):
    """Base exception for sheets manager errors."""
    pass


class CredentialsError(SheetsManagerError):
    """Raised when credentials are missing or invalid."""
    pass


class TemplateNotFoundError(SheetsManagerError):
    """Raised when template sheet cannot be found."""
    pass


class SheetOperationError(SheetsManagerError):
    """Raised when sheet operation fails."""
    pass


class RateLimitError(SheetsManagerError):
    """Raised when rate limit is exceeded after retries."""
    pass


# Tab names for each template type
TAB_NAMES = {
    "aggregators": "Aggregators Template",
    "opr": "OPR Template",
    "mpp": "MPP Template",
    "adop": "ADOP Template",
    "adre": "ADRE Template",
    "commercial": "Commercial Project Template",
}

# Common field to cell mapping for backward compatibility (tests expect this)
# This is a legacy mapping - the actual implementation uses get_cell_mapping()
# which loads from field_row_mappings.json and maps to column C (EN)
COMMON_FIELD_MAPPING: dict[str, str] = {
    # SEO fields
    "meta_title": "B2",
    "meta_description": "B3",
    "h1": "B4",
    "url_slug": "B5",
    # Content fields
    "short_description": "B6",
    "long_description": "B7",
    "location_description": "B8",
    "amenities_description": "B9",
    "payment_plan_description": "B10",
    "investment_highlights": "B11",
    # Project data fields
    "project_name": "B12",
    "developer": "B13",
    "location": "B14",
    "starting_price": "B15",
    "bedrooms": "B16",
    "completion_date": "B17",
    "property_type": "B18",
}


class SheetsManager:
    """
    Google Sheets integration service.

    Manages template copying, content population, validation,
    and permission management for Google Sheets in Shared Drive.
    """

    # Rate limiting configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 16.0  # seconds

    def __init__(self):
        """Initialize sheets manager with gspread client."""
        self.settings = get_settings()
        self.client = self._init_gspread_client()
        logger.info("SheetsManager initialized")

    def _init_gspread_client(self) -> gspread.Client:
        """
        Initialize gspread client with service account credentials.

        Returns:
            Authenticated gspread client

        Raises:
            CredentialsError: If credentials are missing or invalid
        """
        try:
            credentials_path = self.settings.GOOGLE_APPLICATION_CREDENTIALS

            if not credentials_path:
                raise CredentialsError(
                    "GOOGLE_APPLICATION_CREDENTIALS not configured. "
                    "Please set the path to your service account key file."
                )

            # Define required scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive',
            ]

            # Load credentials
            creds = Credentials.from_service_account_file(
                credentials_path,
                scopes=scopes
            )

            # Initialize client with request timeout
            client = gspread.authorize(creds)
            # Set a 30-second timeout on the underlying HTTP session
            client.http_client.session.timeout = 30

            logger.info("gspread client initialized successfully")
            return client

        except FileNotFoundError as e:
            raise CredentialsError(
                f"Service account credentials file not found: {credentials_path}"
            ) from e
        except Exception as e:
            raise CredentialsError(
                f"Failed to initialize gspread client: {str(e)}"
            ) from e

    def _get_field_mapping(
        self,
        template_type: str,
        language: str = "en"
    ) -> dict[str, str]:
        """
        Get field to cell mapping for a template type.

        Column structure: A=Guidelines, B=Field Label, C=EN, D=AR, E=RU
        Uses field_row_mappings.json as source of truth for row numbers.

        Args:
            template_type: Template type (aggregators, opr, mpp, adop, adre, commercial)
            language: Language code - "en", "ar", or "ru" (default: "en")

        Returns:
            Dictionary mapping field names to cell references (e.g., {"meta_title": "C4"})

        Raises:
            ValueError: If template type or language is invalid
        """
        # Validate template type
        try:
            TemplateType(template_type.lower())
        except ValueError:
            valid_types = [t.value for t in TemplateType]
            raise ValueError(
                f"Invalid template type: {template_type}. "
                f"Valid types: {valid_types}"
            )

        # Get mapping from template_fields module (uses field_row_mappings.json)
        return get_cell_mapping(template_type, language)

    def _exponential_backoff(
        self,
        attempt: int,
        base_delay: float = INITIAL_RETRY_DELAY
    ) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Current attempt number (0-indexed)
            base_delay: Base delay in seconds

        Returns:
            Delay in seconds (capped at MAX_RETRY_DELAY)
        """
        delay = min(base_delay * (2 ** attempt), self.MAX_RETRY_DELAY)
        return delay

    def _retry_operation(self, operation_name: str, func, *args, **kwargs):
        """
        Retry operation with exponential backoff.

        Handles Google Sheets API rate limits (429 errors) and transient failures.

        Args:
            operation_name: Name of operation for logging
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution

        Raises:
            RateLimitError: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                last_exception = e

                # Check if it's a rate limit error (429)
                if hasattr(e, 'response') and e.response.status_code == 429:
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self._exponential_backoff(attempt)
                        logger.warning(
                            f"{operation_name} rate limited, "
                            f"retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        time.sleep(delay)
                        continue

                # For other API errors, fail immediately
                raise
            except Exception as e:
                # For non-API errors, retry with backoff
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(
                        f"{operation_name} failed, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self.MAX_RETRIES}): {str(e)}"
                    )
                    time.sleep(delay)
                    continue
                raise

        # All retries exhausted
        raise RateLimitError(
            f"{operation_name} failed after {self.MAX_RETRIES} attempts"
        ) from last_exception

    async def create_project_sheet(
        self,
        project_name: str,
        template_type: str
    ) -> SheetResult:
        """
        Create a new project sheet from template.

        Copies the template sheet to Shared Drive and sets title.

        Args:
            project_name: Name for the new sheet
            template_type: Template type to copy from

        Returns:
            SheetResult with sheet details

        Raises:
            TemplateNotFoundError: If template sheet not found
            SheetOperationError: If sheet creation fails
        """
        return await asyncio.to_thread(
            self._create_project_sheet_sync,
            project_name,
            template_type
        )

    def _create_project_sheet_sync(
        self,
        project_name: str,
        template_type: str
    ) -> SheetResult:
        """Synchronous implementation of create_project_sheet."""
        return self._retry_operation(
            "create_project_sheet",
            self._create_project_sheet_impl,
            project_name,
            template_type
        )

    def _create_project_sheet_impl(
        self,
        project_name: str,
        template_type: str
    ) -> SheetResult:
        """Implementation of create_project_sheet without retry logic."""
        try:
            # Get template sheet ID
            template_id = self.settings.get_template_sheet_id(template_type)

            logger.info(
                f"Creating sheet '{project_name}' from template '{template_type}' ({template_id})"
            )

            # Verify template sheet exists (raises if not found)
            try:
                self.client.open_by_key(template_id)
            except SpreadsheetNotFound as e:
                raise TemplateNotFoundError(
                    f"Template sheet not found: {template_type} ({template_id})"
                ) from e

            # Copy to Shared Drive
            folder_id = self.settings.GOOGLE_DRIVE_ROOT_FOLDER_ID

            # Copy the spreadsheet
            copied_sheet = self.client.copy(
                file_id=template_id,
                title=project_name,
                folder_id=folder_id
            )

            sheet_id = copied_sheet.id
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            created_at = datetime.now(timezone.utc).isoformat()

            logger.info(
                f"Sheet created successfully: {sheet_id}",
                extra={
                    "sheet_id": sheet_id,
                    "project_name": project_name,
                    "template_type": template_type
                }
            )

            return SheetResult(
                sheet_id=sheet_id,
                sheet_url=sheet_url,
                title=project_name,
                template_type=template_type,
                created_at=created_at
            )

        except (TemplateNotFoundError, RateLimitError):
            raise
        except Exception as e:
            raise SheetOperationError(
                f"Failed to create project sheet: {str(e)}"
            ) from e

    async def populate_sheet(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> PopulateResult:
        """
        Populate sheet with content using batch update.

        Maps content fields to cells and updates in a single API call.

        Args:
            sheet_id: Target sheet ID
            content: Dictionary of field_name -> value
            template_type: Template type for field mapping

        Returns:
            PopulateResult with success/failure counts

        Raises:
            SheetOperationError: If population fails
        """
        return await asyncio.to_thread(
            self._populate_sheet_sync,
            sheet_id,
            content,
            template_type
        )

    def _populate_sheet_sync(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> PopulateResult:
        """Synchronous implementation of populate_sheet."""
        return self._retry_operation(
            "populate_sheet",
            self._populate_sheet_impl,
            sheet_id,
            content,
            template_type
        )

    def _populate_sheet_impl(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> PopulateResult:
        """Implementation of populate_sheet without retry logic."""
        try:
            # Get field mapping for English (column C)
            field_mapping = self._get_field_mapping(template_type, language="en")

            # Open sheet and get correct worksheet by tab name
            try:
                spreadsheet = self.client.open_by_key(sheet_id)
                tab_name = TAB_NAMES.get(template_type.lower())
                if tab_name:
                    worksheet = spreadsheet.worksheet(tab_name)
                else:
                    worksheet = spreadsheet.sheet1  # Fallback for unknown types
            except SpreadsheetNotFound as e:
                raise SheetOperationError(
                    f"Sheet not found: {sheet_id}"
                ) from e

            # Prepare batch update data
            updates = []
            failures = []
            fields_written = 0

            for field_name, cell_ref in field_mapping.items():
                if field_name in content:
                    value = content[field_name]

                    # Skip None or empty values
                    if value is None or value == "":
                        continue

                    try:
                        updates.append({
                            'range': cell_ref,
                            'values': [[str(value)]]
                        })
                        fields_written += 1
                    except Exception as e:
                        failures.append({
                            'field': field_name,
                            'cell': cell_ref,
                            'error': str(e)
                        })

            # Execute batch update
            if updates:
                logger.info(f"Updating {len(updates)} cells in sheet {sheet_id}")
                worksheet.batch_update(updates)

            logger.info(
                f"Sheet populated: {fields_written} fields written, {len(failures)} failures",
                extra={
                    "sheet_id": sheet_id,
                    "fields_written": fields_written,
                    "fields_failed": len(failures)
                }
            )

            return PopulateResult(
                sheet_id=sheet_id,
                total_fields=len(field_mapping),
                fields_written=fields_written,
                fields_failed=len(failures),
                failures=failures
            )

        except (SheetOperationError, RateLimitError):
            raise
        except Exception as e:
            raise SheetOperationError(
                f"Failed to populate sheet: {str(e)}"
            ) from e

    async def read_back_validate(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> ValidationResult:
        """
        Read values back from sheet and validate against expected content.

        Args:
            sheet_id: Sheet ID to validate
            content: Expected content dictionary
            template_type: Template type for field mapping

        Returns:
            ValidationResult with match/mismatch details

        Raises:
            SheetOperationError: If validation fails
        """
        return await asyncio.to_thread(
            self._read_back_validate_sync,
            sheet_id,
            content,
            template_type
        )

    def _read_back_validate_sync(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> ValidationResult:
        """Synchronous implementation of read_back_validate."""
        return self._retry_operation(
            "read_back_validate",
            self._read_back_validate_impl,
            sheet_id,
            content,
            template_type
        )

    def _read_back_validate_impl(
        self,
        sheet_id: str,
        content: dict[str, str],
        template_type: str
    ) -> ValidationResult:
        """Implementation of read_back_validate without retry logic."""
        try:
            # Get field mapping for English (column C)
            field_mapping = self._get_field_mapping(template_type, language="en")

            # Open sheet and get correct worksheet by tab name
            try:
                spreadsheet = self.client.open_by_key(sheet_id)
                tab_name = TAB_NAMES.get(template_type.lower())
                if tab_name:
                    worksheet = spreadsheet.worksheet(tab_name)
                else:
                    worksheet = spreadsheet.sheet1  # Fallback for unknown types
            except SpreadsheetNotFound as e:
                raise SheetOperationError(
                    f"Sheet not found: {sheet_id}"
                ) from e

            # Build list of cells to read and batch-fetch (P3-17)
            cells_to_check = []
            for field_name, cell_ref in field_mapping.items():
                if field_name in content:
                    expected = str(content[field_name]) if content[field_name] is not None else ""
                    if expected != "":
                        cells_to_check.append((field_name, cell_ref, expected))

            # Batch read all cells at once to avoid N individual API calls
            cell_refs = [item[1] for item in cells_to_check]
            batch_values = {}
            try:
                if cell_refs:
                    batch_result = worksheet.batch_get(cell_refs)
                    for i, cell_ref in enumerate(cell_refs):
                        if i < len(batch_result) and batch_result[i]:
                            batch_values[cell_ref] = batch_result[i][0][0] if batch_result[i][0] else ""
                        else:
                            batch_values[cell_ref] = ""
            except Exception as batch_err:
                logger.warning("Batch get failed, falling back to individual reads: %s", batch_err)
                for cell_ref in cell_refs:
                    try:
                        batch_values[cell_ref] = worksheet.acell(cell_ref).value or ""
                    except Exception as e:
                        batch_values[cell_ref] = f"ERROR: {str(e)}"

            details = []
            matches = 0
            mismatches = 0

            for field_name, cell_ref, expected in cells_to_check:
                actual = batch_values.get(cell_ref, "")
                is_error = isinstance(actual, str) and actual.startswith("ERROR:")

                if is_error:
                    match = False
                    mismatches += 1
                else:
                    match = (str(actual).strip() == expected.strip())
                    if match:
                        matches += 1
                    else:
                        mismatches += 1

                details.append({
                    'field': field_name,
                    'cell': cell_ref,
                    'expected': expected,
                    'actual': actual,
                    'match': match
                })

            logger.info(
                f"Validation complete: {matches} matches, {mismatches} mismatches",
                extra={
                    "sheet_id": sheet_id,
                    "matches": matches,
                    "mismatches": mismatches
                }
            )

            return ValidationResult(
                sheet_id=sheet_id,
                total_checked=len(details),
                matches=matches,
                mismatches=mismatches,
                details=details
            )

        except (SheetOperationError, RateLimitError):
            raise
        except Exception as e:
            raise SheetOperationError(
                f"Failed to validate sheet: {str(e)}"
            ) from e

    async def share_sheet(
        self,
        sheet_id: str,
        email: str,
        role: str = "writer"
    ) -> bool:
        """
        Share sheet with a user.

        Args:
            sheet_id: Sheet ID to share
            email: Email address of user to share with
            role: Permission role (reader, writer, owner)

        Returns:
            True if sharing succeeded

        Raises:
            SheetOperationError: If sharing fails
        """
        return await asyncio.to_thread(
            self._share_sheet_sync,
            sheet_id,
            email,
            role
        )

    def _share_sheet_sync(
        self,
        sheet_id: str,
        email: str,
        role: str = "writer"
    ) -> bool:
        """Synchronous implementation of share_sheet."""
        return self._retry_operation(
            "share_sheet",
            self._share_sheet_impl,
            sheet_id,
            email,
            role
        )

    def _share_sheet_impl(
        self,
        sheet_id: str,
        email: str,
        role: str = "writer"
    ) -> bool:
        """Implementation of share_sheet without retry logic."""
        try:
            # Validate role
            valid_roles = ['reader', 'writer', 'owner']
            if role not in valid_roles:
                raise ValueError(
                    f"Invalid role: {role}. Valid roles: {valid_roles}"
                )

            # Open sheet
            try:
                spreadsheet = self.client.open_by_key(sheet_id)
            except SpreadsheetNotFound as e:
                raise SheetOperationError(
                    f"Sheet not found: {sheet_id}"
                ) from e

            # Share the sheet
            spreadsheet.share(email, perm_type='user', role=role)

            logger.info(
                f"Sheet shared with {email} as {role}",
                extra={
                    "sheet_id": sheet_id,
                    "email": email,
                    "role": role
                }
            )

            return True

        except (SheetOperationError, RateLimitError):
            raise
        except Exception as e:
            raise SheetOperationError(
                f"Failed to share sheet: {str(e)}"
            ) from e

    async def validate_templates(self) -> dict[str, bool]:
        """
        Validate that all 6 template sheets are accessible.

        Call at startup or before job execution to catch missing/deleted
        templates early rather than failing mid-pipeline.

        Returns:
            Dict mapping template_type -> accessible (True/False)
        """
        return await asyncio.to_thread(self._validate_templates_sync)

    def _validate_templates_sync(self) -> dict[str, bool]:
        """Synchronous implementation of validate_templates."""
        results = {}
        template_types = ["aggregators", "opr", "mpp", "adop", "adre", "commercial"]

        for template_type in template_types:
            try:
                template_id = self.settings.get_template_sheet_id(template_type)
                self.client.open_by_key(template_id)
                results[template_type] = True
                logger.info("Template '%s' accessible: %s", template_type, template_id)
            except SpreadsheetNotFound:
                results[template_type] = False
                logger.error("Template '%s' NOT FOUND: %s", template_type, template_id)
            except Exception as e:
                results[template_type] = False
                logger.error("Template '%s' validation failed: %s", template_type, e)

        accessible = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info("Template validation complete: %d/%d accessible", accessible, total)

        return results
