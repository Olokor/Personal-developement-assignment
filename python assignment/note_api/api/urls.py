from django.urls import path

from api import views

urlpatterns = [
    path("", views.getRoutes, name="routes"),
    path("notes/", views.getNotes, name="notes"),
    path("notes/<int:pk>", views.getNote, name="note"),
    path("notes/update/<int:pk>", views.updateNote, name="updateNote"),
    path("notes/delete/<int:pk>", views.deleteNote, name="updateNote"),
    path("notes/create", views.createNote, name="createNote"),

]