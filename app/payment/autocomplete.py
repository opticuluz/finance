from dal import autocomplete
from tag.models import Tag


class TagAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Tag.objects.none()

        if self.request.user.is_superuser:
            queryset = Tag.objects.filter(active=True)
        else:
            queryset = Tag.objects.filter(user=self.request.user, active=True)

        if self.q:
            queryset = queryset.filter(tag_name__icontains=self.q)

        return queryset
