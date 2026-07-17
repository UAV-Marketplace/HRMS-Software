from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from geopy.distance import geodesic
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from base.models import Company
from geofencing.forms import GeoFencingSetupForm

from .models import GeoFencing
from .serializers import *


class GeoFencingSetupGetPostAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        permission_required("geofencing.view_geofencing", raise_exception=True),
        name="dispatch",
    )
    def get(self, request):
        company = request.user.employee_get.get_company()
        locations = GeoFencing.objects.filter(company_id=company)
        serializer = GeoFencingSetupSerializer(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @method_decorator(
        permission_required("geofencing.add_geofencing", raise_exception=True),
        name="dispatch",
    )
    def post(self, request):
        data = request.data
        if not request.user.is_superuser:
            if isinstance(data, QueryDict):
                data = data.dict()
            company = request.user.employee_get.get_company()
            if company:
                data["company_id"] = company.id
        serializer = GeoFencingSetupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GeoFencingSetupPutDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        permission_required("geofencing.change_geofencing", raise_exception=True),
        name="dispatch",
    )
    def put(self, request, pk):
        location = get_object_or_404(GeoFencing, pk=pk)
        company = request.user.employee_get.get_company()
        if request.user.is_superuser or company == location.company_id:
            serializer = GeoFencingSetupSerializer(
                location, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        raise serializers.ValidationError("Access Denied..")

    @method_decorator(
        permission_required("geofencing.delete_geofencing", raise_exception=True),
        name="dispatch",
    )
    def delete(self, request, pk):
        location = get_object_or_404(GeoFencing, pk=pk)
        company = request.user.employee_get.get_company()
        if request.user.is_superuser or company == location.company_id:
            location.delete()
            return Response(
                {"message": "GeoFencing location deleted successfully"},
                status=status.HTTP_200_OK,
            )
        raise serializers.ValidationError("Access Denied..")


class GeoFencingEmployeeLocationCheckAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, request):
        try:
            company = request.user.employee_get.get_company()
            return company
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_active_company_locations(self, request):
        company = self.get_company(request)
        return list(GeoFencing.objects.filter(company_id=company, start=True))

    def post(self, request):
        serializer = EmployeeLocationSerializer(data=request.data)
        active_locations = self.get_active_company_locations(request)
        if not active_locations:
            raise serializers.ValidationError("Geofencing is not yet started..")
        if serializer.is_valid():
            employee_location = (
                request.data.get("latitude"),
                request.data.get("longitude"),
            )
            for company_location in active_locations:
                geofence_center = (
                    company_location.latitude,
                    company_location.longitude,
                )
                distance = geodesic(geofence_center, employee_location).meters
                if distance <= company_location.radius_in_meters:
                    return Response(
                        {"message": "Inside the geofence"}, status=status.HTTP_200_OK
                    )
            return Response(
                {"message": "Outside the geofence"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GeoFencingSetUpPermissionCheck(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(
        permission_required("geofencing.view_geofencing", raise_exception=True),
        name="dispatch",
    )
    def get(self, request):
        return Response(status=200)


def get_company(request):
    try:
        selected_company = request.session.get("selected_company")
        if selected_company == "all":
            return None
        company = Company.objects.get(id=selected_company)
        return company
    except Exception as e:
        raise serializers.ValidationError(e)


def get_company_locations(request):
    company = get_company(request)
    return GeoFencing.objects.filter(company_id=company).order_by("-id")


def geofencing_table_response(request, success_message):
    """
    Closes any open geofencing modal and pushes a fresh copy of the location
    table into #geo via an out-of-band swap.
    """
    messages.success(request, success_message)
    table_html = render_to_string(
        "geo_config.html",
        {"locations": get_company_locations(request), "messages": messages.get_messages(request)},
        request=request,
    )
    return HttpResponse(
        "<script>$('.oh-modal--show').removeClass('oh-modal--show');</script>"
        f'<div id="geo" hx-swap-oob="true">{table_html}</div>'
    )


@login_required
@permission_required("geofencing.add_localbackup")
def geo_location_config(request):
    locations = get_company_locations(request)
    return render(request, "geo_config.html", {"locations": locations})


@login_required
@permission_required("geofencing.add_geofencing")
def create_geofencing(request):
    if request.method == "POST":
        data = request.POST
        if isinstance(data, QueryDict):
            data = data.dict()
        company = get_company(request)
        data["company_id"] = company.id if company else None
        form = GeoFencingSetupForm(data=data)
        if form.is_valid():
            form.save()
            return geofencing_table_response(
                request, _("Geofence location added successfully.")
            )
    else:
        form = GeoFencingSetupForm()
    return render(request, "geo_config_form.html", {"form": form})


@login_required
@permission_required("geofencing.change_geofencing")
def update_geofencing(request, pk):
    location = get_object_or_404(GeoFencing, pk=pk)
    if request.method == "POST":
        form = GeoFencingSetupForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return geofencing_table_response(
                request, _("Geofence location updated successfully.")
            )
    else:
        form = GeoFencingSetupForm(instance=location)
    return render(request, "geo_config_form.html", {"form": form, "location": location})


@login_required
@permission_required("geofencing.delete_geofencing")
def delete_geofencing(request, pk):
    location = get_object_or_404(GeoFencing, pk=pk)
    location.delete()
    messages.success(request, _("Geofence location deleted successfully."))
    locations = get_company_locations(request)
    return render(request, "geo_config.html", {"locations": locations})
