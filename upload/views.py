from django.shortcuts import render, redirect
from .models import UploadKey, Upload, UploadLaufband
from .forms import UploadForm, UploadLaufbandForm
from django.views.decorators.csrf import csrf_exempt
import os
from pdf2image import convert_from_path
from django.conf import settings
import uuid


@csrf_exempt
def upload(request, key):
    db_keys = UploadKey.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if not keycheck:
        return redirect('/')

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # delete old objects and their pdf files
            obj = Upload.objects.filter(name=request.POST.get("name"))
            for i in obj:
                try:
                    if os.path.exists(i.file.path):
                        os.remove(i.file.path)
                except Exception as e:
                    print(e)
                i.delete()
            instance = form.save()
            # set output directory and create if necessary
            output_directory = os.path.join(settings.MEDIA_ROOT, instance.name)
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            else:
                # Delete old images in the directory
                for old_image in os.listdir(output_directory):
                    old_image_path = os.path.join(output_directory, old_image)
                    if os.path.isfile(old_image_path):
                        os.remove(old_image_path)
            # Convert PDF to images
            if instance.file and instance.file.name.endswith(".pdf"):
                images = convert_from_path(instance.file.path, dpi=150)
                for i, image in enumerate(images):
                    # Save images in the pdf as png
                    uid = uuid.uuid4()
                    image_path = os.path.join(
                        output_directory, f"image{i:02d}_{uid}.png"
                    )
                    image.save(image_path, "PNG")
            else:
                print("ERROR! NOT A PDF FILE!")
            return redirect("upload", key=key)

    form = UploadForm()
    return render(request, "upload.html", {"form": form, "key": key})


@csrf_exempt
def upload_laufband(request, key):
    db_keys = UploadKey.objects.all()
    keycheck = False
    for db_key in db_keys:
        if key == db_key.key:
            keycheck = True

    if not keycheck:
        return redirect('/')

    if request.method == "POST":
        form = UploadLaufbandForm(request.POST)
        if form.is_valid():
            try:
                obj = UploadLaufband.objects.get(name=request.POST.get("name"))
                obj.delete()
            except UploadLaufband.DoesNotExist:
                pass
            form.save()
        return redirect("upload_laufband", key=key)

    form = UploadLaufbandForm()
    return render(request, "upload_laufband.html", {"form": form, "key": key})
