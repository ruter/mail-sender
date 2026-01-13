class TemplateRenderer:
    @staticmethod
    def render(owner: str, month: str, body_template: str, signature: str) -> str:
        body_html = body_template.replace("{owner}", owner).replace("{month}", month)
        
        if signature:
            return f"""<div>{body_html}</div><br><div>{signature}</div>"""
        
        return f"<div>{body_html}</div>"
    
    @staticmethod
    def render_subject(month: str, subject_template: str) -> str:
        """Render subject line with month variable."""
        return subject_template.replace("{month}", month)
