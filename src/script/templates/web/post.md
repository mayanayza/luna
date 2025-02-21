{% if project.github %}
  [View on GitHub]({{ project.github }}){:target="_blank"}
{% endif %}
{{ content }}
{% raw %}
{% include iframe-embed.html iframe_embed=page.iframe_embeds %}
{% endraw %}
{% raw %}
{% include gallery.html images=page.images %}
{% endraw %}
{% raw %}
{% include video.html videos=page.videos %}
{% endraw %}
{% raw %}
{% include model-viewer.html models=page.models %}
{% endraw %}
{% raw %}
{% include monster-food.html id=page.name %}
{% endraw %}