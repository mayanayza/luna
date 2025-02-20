---
layout: page
title: Maya's Links
permalink: /links/
hide_header: true
---

{% raw %}
{% if site.data.settings.social %}
<div class="social">
  <ul class="social__list list-reset">
    {% for social in site.data.settings.social %}
    <li class="social__item">
      <a class="social__link" href="{{ social.link }}" target="_blank" rel="noopener" aria-label="{{ social.name }} link"><i class="{{ social.icon }}"></i></a>
    </li>
    {% endfor %}
  </ul>
</div>
{% endif %}
{% endraw %}
<br />
<div class="links-container" style="display: flex; flex-direction: column; align-items: center; gap: 1rem; width: 100%;">

{% if featured %}
<h2>Featured</h2>

{% for project in featured %}
<div class="button button--primary" style="width: 100%; display: flex; align-items: center; padding: 0; height: 4.5rem; position: relative;" onclick="window.open('{{ project.website }}', '_blank')">
  {% if project.image %}
  <div class="button-image" style="height: 100%; margin: 0; padding: 0; position: absolute; left: 0;">
    <img src="{{ project.image }}" alt="{{ project.name }}" style="height: 4.5rem; width: auto; margin: 0; padding: 0; display: block;">
  </div>
  {% endif %}
  <span style="flex: 1; text-align: center; padding: 0.5rem;">{{ project.title }}</span>
</div>
{% endfor %}
<br />
{% endif %}

{% if in_progress %}
<h2>In the Works</h2>

<table>
  <tbody>
    {% for project in in_progress %}
    <tr>
      <td>
        {% if project.github %}
        <a href='{{ project.github }}' target='_blank'>{{ project.display_name }}</a>
        {% else %}
        {{ project.display_name }}
        {% endif %}
      </td>
      <td>{{ project.tagline | default('') }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% else %}
Nothing currently in progress
{% endif %}

<!-- <div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://dev.to/mayanayza', '_blank')">Dev.to</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://cara.app/mayanayza/', '_blank')">Cara</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://hackaday.io/mayanayza', '_blank')">Hackaday.io</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://www.hackster.io/mayanayza', '_blank')">Hackster.io</div>
</div> -->