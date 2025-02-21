{% if project.github %}
  [View on GitHub]({{ project.github }}){:target="_blank"}
{% endif %}
{{ page.written_content }}
{% include iframe-embed.html iframe_embed=page.iframe_embeds %}
{% include gallery.html images=page.images %}
{% include video.html videos=page.videos %}
{% include model-viewer.html models=page.models %}
{% include monster-food.html id=page.name %}