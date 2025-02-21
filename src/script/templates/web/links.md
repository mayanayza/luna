## Featured

{% include featured-links.html projects=page.featured_projects %}
{% include button.html link=page.website title="View Portfolio" %}

## In the Works

{% include roadmap-entries.html entries=page.in_progress empty_message="Nothing currently in progress" %}
{% capture roadmap_url %}{{ page.website }}/roadmap{% endcapture %}
{% include button.html link=roadmap_url title="View Roadmap" %}