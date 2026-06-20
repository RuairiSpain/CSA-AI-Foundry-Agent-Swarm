# Document Writer Agent

## Overview

The Document Writer agent generates professional Word documents (.docx) from structured data.

Input a document structure (title, sections, formatting), and receive a properly formatted .docx file ready to share, print, or archive.

Perfect for: reports, contracts, proposals, client deliverables, formatted exports.

## Contract Specification

### Inputs

**document_data** (object) - Structure defining the document:
- `title` (string, required): Document title
- `author` (string, optional): Author name
- `subject` (string, optional): Document subject
- `sections` (array, required): Document sections
  - `heading` (string): Section heading
  - `content` (string): Section body (Markdown or plain text)
  - `style` (string): Visual style (normal, highlight, note, code)
  - `include_page_break` (boolean): Page break before section

### Outputs

**document** (object) - Generated Word document:
- `filename` (string): Suggested filename
- `content_base64` (string): Base64-encoded .docx file
- `size_bytes` (integer): File size
- `page_count` (integer): Number of pages
- `metadata` (object): Generation metadata

## Usage

### Basic Example

```python
from agents.document_writer import DocumentWriter

agent = DocumentWriter()

result = await agent.invoke({
    "document_data": {
        "title": "Sales Report Q2 2026",
        "author": "Sales Team",
        "sections": [
            {
                "heading": "Executive Summary",
                "content": "Strong growth in key markets.",
                "style": "highlight"
            },
            {
                "heading": "Regional Breakdown",
                "content": "North America: +20%\nEurope: +15%\nAsia: +18%",
                "style": "normal",
                "include_page_break": True
            }
        ]
    }
})

# Decode and save
import base64
if result["status"] == "success":
    content = base64.b64decode(result["document"]["content_base64"])
    with open(result["document"]["filename"], "wb") as f:
        f.write(content)
```

## Use Cases

1. **Client Reports** - Generate formatted reports for clients
2. **Contract Generation** - Create standardized contracts
3. **Proposal Documents** - Professional proposals with styling
4. **Analysis Exports** - Export analysis results as documents
5. **Documentation** - Generate technical documentation

## Configuration

### Styling Options

- `normal`: Regular paragraph style
- `highlight`: Highlighted/callout style
- `note`: Note/important box style
- `code`: Code block with monospace font

### Page Breaks

Use `include_page_break: true` to start a new page before a section:

```json
{
  "heading": "Chapter 2",
  "content": "...",
  "include_page_break": true
}
```

## Dependencies

- **python-docx >= 0.8.10** - Word document generation
- **pandas >= 1.0** - Data manipulation support

## Limitations

- Maximum 100 sections per document
- 50MB maximum output file size
- Requires pre-structured input (not freeform)
- Output is Base64 encoded (must be decoded)
- Limited formatting options (expand by modifying scripts/)

## Error Handling

Returns error status when:
- Input validation fails (missing required fields)
- Document generation fails
- Output exceeds file size limit
- Encoding error occurs

Example error response:
```json
{
  "status": "error",
  "error_message": "Input validation failed: missing required field 'sections'"
}
```

## Advanced Usage

### Custom Formatting

Modify `scripts/formatter.py` to add:
- Custom styles
- Header/footer
- Embedded images
- Tables
- Bullet points
- Text formatting

### Batch Generation

Generate multiple documents in sequence:

```python
documents = [
    {"title": "Report 1", ...},
    {"title": "Report 2", ...},
    {"title": "Report 3", ...}
]

for doc_data in documents:
    result = await agent.invoke({"document_data": doc_data})
    # Process result
```

## Related Agents

- **presenter-html** - Generate HTML dashboards
- **presenter-markdown** - Generate Markdown output
- **presenter-word** - Word document formatting
- **presenter-code** - Code generation

## Tips

1. **Keep sections focused** - One idea per section
2. **Use meaningful headings** - Help readers navigate
3. **Structure content** - Use Markdown for lists and formatting
4. **Include metadata** - Author and subject for document properties
5. **Test styling** - Preview with different styles

## Troubleshooting

**File too large:**
- Reduce number of sections
- Shorten section content
- Remove large data blocks

**Style not applied:**
- Ensure valid style name (normal, highlight, note, code)
- Check section structure matches contract

**Decoding error:**
- Verify Base64 content is complete
- Check for encoding issues

## Testing

```bash
# Show agent details
python -m safe_cli.cli show-agent document-writer

# Validate contract
python -m safe_cli.cli validate-agent \
  --agent agents/document-writer \
  --pattern sequential-pipeline \
  --placeholder presenter

# Create from template
python -m safe_cli.cli create-agent --from-template document-writer
```

## Performance

- Average generation time: 2-5 seconds
- Memory usage: ~50-100MB depending on document size
- Timeout: 120 seconds

---

**Status:** Production Ready  
**Version:** 1.0  
**Framework:** SAFE 1.0  
**Last Updated:** 2026-06-20
