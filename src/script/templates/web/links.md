## Featured

{% include featured-links.html projects=page.featured_projects %}
{% capture portfolio_url %}{{ page.website }}/tags/?tag=art{% endcapture %}
{% include button.html link=portfolio_url title="View Art Portfolio" %}
{% include button.html link=page.website title="View All Work" %}

## In the Works

{% include roadmap-entries.html entries=page.in_progress empty_message="Nothing currently in progress" %}
{% capture roadmap_url %}{{ page.website }}/roadmap{% endcapture %}
{% include button.html link=roadmap_url title="View Roadmap" %}