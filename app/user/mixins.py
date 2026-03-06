class UserRestrictedAdminMixin:
    """
    Ограничивает доступ к записям обычного пользователя.
    Работает как для моделей с полем `user`,
    так и для связанных моделей через `related_field` (например, payment.user).
    """

    # Если модель не имеет поле user напрямую, укажи связанное поле
    related_user_field = None  # Например: 'payment__user'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset

        if self.related_user_field:
            filter_kwargs = {self.related_user_field: request.user}
            return queryset.filter(**filter_kwargs)
        elif hasattr(self.model, "user"):
            return queryset.filter(user=request.user)
        return queryset

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        if not request.user.is_superuser:
            # Скрываем фильтр по пользователю для обычных
            list_filter = [f for f in list_filter if f != 'user']
        return list_filter

    def save_model(self, request, obj, form, change):
        if hasattr(obj, "user_id") and not obj.user_id:
            obj.user_id = request.user.pk
        super().save_model(request, obj, form, change)
