# {{ project.display_name }}

{{ content }}

## Media

{% if images %}
### Images
{% for image in images %}
![{{ image.stem }}](media/images/{{ image.name }})
{% endfor %}
{% endif %}

{% if videos %}
### Videos
{% for video in videos %}
- [{{ video.stem }}](media/videos/{{ video.name }})
{% endfor %}
{% endif %}

{% if models %}
### 3D Models
{% for model in models %}
- [{{ model.stem }}](media/models/{{ model.name }})
{% endfor %}
{% endif %}