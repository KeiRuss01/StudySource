from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .image_forms import ResearchImageForm
from .models import ResearchFolder, ResearchImage, User
from .services.cloudinary import CloudinaryError, configured, delete_image, upload_image


def require_student(request):
    if request.user.role != User.Role.STUDENT:
        raise PermissionDenied


@login_required
@require_http_methods(["GET", "POST"])
def image_upload(request, folder_id):
    require_student(request)
    folder = get_object_or_404(ResearchFolder, id=folder_id, owner=request.user)
    if not configured():
        messages.error(request, "Cloudinary credentials are not configured yet.")
        return redirect("folder_detail", folder_id=folder.id)
    form = ResearchImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            data = upload_image(
                form.cleaned_data["image"],
                f"studysource/{request.user.id}/{folder.id}",
            )
            ResearchImage.objects.create(
                owner=request.user,
                folder=folder,
                title=form.cleaned_data["title"].strip(),
                image_url=data["secure_url"],
                public_id=data["public_id"],
            )
            messages.success(request, "Image uploaded successfully.")
            return redirect("folder_detail", folder_id=folder.id)
        except CloudinaryError as error:
            messages.error(request, str(error))
    return render(request, "study/images/image_form.html", {
        "form": form,
        "folder": folder,
    })


@login_required
@require_http_methods(["POST"])
def image_delete(request, image_id):
    require_student(request)
    image = get_object_or_404(ResearchImage, id=image_id, owner=request.user)
    folder_id = image.folder_id
    try:
        delete_image(image.public_id)
    except CloudinaryError as error:
        messages.error(request, str(error))
        return redirect("folder_detail", folder_id=folder_id)
    image.delete()
    messages.success(request, "Image deleted.")
    return redirect("folder_detail", folder_id=folder_id)
