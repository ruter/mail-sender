class TemplateRenderer:
    @staticmethod
    def render(owner: str, month: str, body_template: str, signature: str) -> str:
        body_html = body_template.replace("{owner}", owner).replace("{month}", month)
        
        if signature:
            return f"""<div>{body_html}</div><br><div>{signature}</div>"""
        
        return f"<div>{body_html}</div>"
