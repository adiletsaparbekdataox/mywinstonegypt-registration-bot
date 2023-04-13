from django.shortcuts import render
from django.views import View


class ReactView(View):
    template_name = "client/index.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)