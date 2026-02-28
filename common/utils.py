from django.utils.text import slugify


def unique_slug(instance, source_text, model_class, slug_field="slug"):
    """
    Generate a unique slug for a model instance.

    Args:
        instance: The model instance being saved
        source_text: The text to slugify (e.g., title, name)
        model_class: The model class to check for uniqueness
        slug_field: The name of the slug field (default: "slug")

    Returns:
        A unique slug string
    """
    base_slug = slugify(source_text)
    slug = base_slug
    counter = 1

    # Build queryset excluding current instance if it has a pk
    queryset = model_class.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    # Keep adding counter until we find a unique slug
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
