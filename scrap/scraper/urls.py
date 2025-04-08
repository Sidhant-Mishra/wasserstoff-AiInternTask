from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login', views.handellogin, name="login"),
    path('logout', views.handlelogout, name="logout"),
    path('allscrap', views.allScraps, name="allscraps"),
    path('scrapdata', views.scrapdata, name="scrapdata"),
    path('linkdin_scrap', views.scrape_linkedin_hr_data, name="linkdin_scrap"),

    path('view-csv/<uuid:excel_id>/', views.view_csv_data, name="view_csv_data"),
]