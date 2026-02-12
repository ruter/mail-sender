import html


class TemplateRenderer:
    @staticmethod
    def render(owner: str, month: str, body_template: str, signature: str) -> str:
        body_html = body_template.replace("{owner}", owner).replace("{month}", month)
        
        if signature:
            # Convert plain text signature to HTML: escape special chars and convert newlines to <br>
            sig_html = html.escape(signature).replace('\n', '<br>')
            return f"""<div>{body_html}</div><br><div>{sig_html}</div>"""
        
        return f"<div>{body_html}</div>"
    
    @staticmethod
    def render_subject(owner: str, month: str, subject_template: str) -> str:
        """Render subject line with owner and month variables."""
        return subject_template.replace("{owner}", owner).replace("{month}", month)
