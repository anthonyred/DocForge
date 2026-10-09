"""Centralized user-facing strings catalog for future internationalization (i18n)."""


class Strings:
    """Application string resources."""

    APP_NAME: str = "DocForge"
    APP_TAGLINE: str = "Professional Markdown to Word Converter"
    
    # Navigation / Views
    TAB_PASTE: str = "Convert Markdown"
    TAB_EDITOR: str = "Profile Editor"
    TAB_LIBRARY: str = "Profile Library"
    TAB_SETTINGS: str = "Settings"

    # Paste View
    MARKDOWN_INPUT_LABEL: str = "Markdown Content:"
    MARKDOWN_PLACEHOLDER: str = "Paste Markdown content here or drag and drop a .md file..."
    PROFILE_SELECT_LABEL: str = "Select Format Profile:"
    OPEN_MARKDOWN_BUTTON: str = "Open .md File"
    SELECT_REFERENCE_BUTTON: str = "Select Reference DOCX"
    CLEAR_REFERENCE_BUTTON: str = "Clear Reference"
    ANALYZE_REFERENCE_BUTTON: str = "Analyze Reference"
    SAVE_REFERENCE_PROFILE_BUTTON: str = "Save Reference Profile"
    USE_SAVED_REFERENCE_BUTTON: str = "Use Saved"
    SAVED_REFERENCE_PLACEHOLDER: str = "Saved reference profiles"
    REFERENCE_PROFILE_NAME_PROMPT: str = "Name this reusable reference profile:"
    REFERENCE_PROFILE_SAVED: str = "Reference profile saved to:\n{path}"
    REFERENCE_PROFILE_SAVE_FAILED: str = "Could not save reference profile: {error}"
    OVERWRITE_OUTPUT_CONFIRM: str = "The output file already exists. Replace it?\n{path}"
    CONVERSION_WARNINGS: str = "Pandoc completed with warnings:\n{warnings}"
    REFERENCE_NOT_SELECTED: str = "No reference DOCX selected."
    REFERENCE_ANALYSIS_LABEL: str = "Reference formatting analysis:"
    REFERENCE_FILE_FILTER: str = "Word Document (*.docx)"
    MARKDOWN_FILE_FILTER: str = "Markdown Files (*.md *.markdown *.txt)"
    REFERENCE_ANALYSIS_FAILED: str = "Could not analyze reference DOCX: {error}"
    REFERENCE_REVIEW_REQUIRED: str = "Review the reference analysis above, then generate again to export."
    GENERATE_BUTTON: str = "Generate .docx Document"
    GENERATE_AND_OPEN_BUTTON: str = "Generate & Open in Word"
    DRAG_DROP_HINT: str = "Drop .md file here to import content"

    # Settings View
    AUTHOR_LABEL: str = "Author Name:"
    AUTHOR_DEFAULT: str = "Anthony Reddy"
    DATE_FORMAT_LABEL: str = "Date Format:"
    DATE_FORMAT_DEFAULT: str = "%B %d, %Y"
    THEME_LABEL: str = "Application Theme:"
    THEME_LIGHT: str = "Light"
    THEME_DARK: str = "Dark"
    THEME_SYSTEM: str = "System"
    SAVE_SETTINGS_BUTTON: str = "Save Settings"
    SETTINGS_SAVED_MSG: str = "Settings saved successfully."

    # Profile Library
    NEW_PROFILE_BUTTON: str = "Create New Profile"
    IMPORT_PROFILE_BUTTON: str = "Import Profile (.json)"
    EXPORT_PROFILE_BUTTON: str = "Export Profile"
    DUPLICATE_PROFILE_BUTTON: str = "Duplicate Profile"
    DELETE_PROFILE_BUTTON: str = "Delete Profile"
    CONFIRM_DELETE_TITLE: str = "Confirm Delete"
    CONFIRM_DELETE_MSG: str = "Are you sure you want to delete profile '{name}'?"

    # Profile Editor
    PROFILE_NAME_LABEL: str = "Profile Name:"
    PROFILE_DESC_LABEL: str = "Description:"
    SECTION_COVER: str = "Cover Page"
    SECTION_BODY: str = "Body Text"
    SECTION_HEADINGS: str = "Headings (H1-H4)"
    SECTION_CODE: str = "Code Blocks & Inline"
    SECTION_TABLES: str = "Tables & Blockquotes"
    SECTION_PAGE: str = "Page Setup & Margins"
    SAVE_PROFILE_BUTTON: str = "Save Format Profile"

    # Dialogs & Notifications
    CONVERSION_SUCCESS_TITLE: str = "Success"
    CONVERSION_SUCCESS_MSG: str = "Document successfully generated:\n{path}"
    ERROR_TITLE: str = "Error"
    ERROR_PARSE_FAILED: str = "Failed to parse Markdown content: {error}"
    ERROR_RENDER_FAILED: str = "Failed to generate Word document: {error}"
    ERROR_INVALID_PROFILE: str = "Invalid format profile JSON: {error}"
