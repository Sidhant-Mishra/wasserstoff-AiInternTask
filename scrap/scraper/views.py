from django.shortcuts import render, redirect
from .scrapylinkdin import TechCompanyScraper
from . models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import pandas as pd
import os
from datetime import datetime
from django.core.paginator import Paginator
from django.conf import settings
from django.http import Http404
import time
import requests
# Create your views here.


def home(request):
    
    return render(request, "home.html")

# def signup(request):
#     if request.method == "POST":

#         name = request.POST.get("name")
#         email = request.POST.get("email")
#         password = request.POST.get("password")
#         re_enter = request.POST.get("re_enter")

#         if password != re_enter:
#             messages.error("password does not match")
#             return redirect("signup")

#         myuser = User.objects.create_user(email=email, name = name, 
#                                       password=password)
        
#         myuser.save()

#         messages.success(request, "account created successfully")
#         return redirect('home')
        

#     return render(request, "signup.html")

def handellogin(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid email or password")
    
    return render(request, "login.html")


def handlelogout(request):
    logout(request)
    messages.success(request, "logout successfully")
    return redirect("home")


# def scrapdata(request):
#     context = {}
    
#     if request.method == "POST":
#         try:
#             # Get search parameters from form (or use defaults)
#             keywords = request.POST.get("keywords", "software developer")
#             location = request.POST.get("location", "remote")
#             num_pages = int(request.POST.get("num_pages", 2))
            
#             # Initialize scraper and run scraping
#             scraper = LinkedInScraper()
#             jobs_df = scraper.scrape_jobs(keywords, location, num_pages=num_pages)
            
#             # Generate a filename with timestamp
#             from datetime import datetime
#             filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
#             # Save the file and create Excel record
#             file_path = f"media/excel/{filename}"
#             jobs_df.to_csv(file_path, index=False)
            
#             # Create Excel model entry with the correct path
#             excel_record = Excel.objects.create(file=f"excel/{filename}")
            
#             # Add results to context for display
#             context['job_count'] = len(jobs_df)
#             context['file_saved'] = True
#             context['excel_id'] = excel_record.id
            
#             messages.success(request, f"Successfully scraped {len(jobs_df)} job listings")
            
#         except Exception as e:
#             messages.error(request, f"Error during scraping: {str(e)}")
#             context['error'] = str(e)
    
#     return render(request, 'scrap.html', context)

def scrapdata(request):
    context = {}
    
    if request.method == "POST":
        try:
            # Get parameters from form
            api_key = request.POST.get("api_key", "")
            search_query = request.POST.get("search_query", "tech companies in India contact site:linkedin.com OR site:crunchbase.com")
            num_pages = int(request.POST.get("num_pages", 5))
            min_companies = int(request.POST.get("min_companies", 100))
            
            if not api_key:
                messages.error(request, "API key is required")
                return render(request, 'tech_scraper.html', context)
            
            # Initialize scraper with parameters
            scraper = TechCompanyScraper(api_key, search_query, num_pages, min_companies)
            
            # Check for existing file
            media_dir = os.path.join('media', 'excel')
            os.makedirs(media_dir, exist_ok=True)
            existing_file = os.path.join(media_dir, "tech_companies_existing.csv")
            
            # Execute scraping process
            companies_df = scraper.run_scraping(existing_file if os.path.exists(existing_file) else None)
            
            # Generate filename with timestamp
            filename = f"tech_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = os.path.join(media_dir, filename)
            
            # Save the file
            companies_df.to_csv(file_path, index=False)
            
            # Also append results to the existing file for future deduplication
            if not os.path.exists(existing_file):
                companies_df.to_csv(existing_file, index=False)
            else:
                # Append without headers
                companies_df.to_csv(existing_file, mode='a', header=False, index=False)
            
            # Create Excel model entry with the correct path
            excel_record = Excel.objects.create(file=f"excel/{filename}")
            
            # Add results to context for display
            context['company_count'] = len(companies_df)
            context['file_saved'] = True
            context['excel_id'] = excel_record.id
            context['file_path'] = os.path.join('excel', filename)
            
            messages.success(request, f"Successfully scraped {len(companies_df)} companies with contact information")
            
        except Exception as e:
            messages.error(request, f"Error during scraping: {str(e)}")
            context['error'] = str(e)
    
    return render(request, 'scrap.html', context)

def scrape_linkedin_hr_data(request):
    context = {}
    
    if request.method == "POST":
        try:
            # Get parameters from form
            api_key = request.POST.get("api_key", "")
            company_query = request.POST.get("company_query", "top tech companies")
            num_companies = int(request.POST.get("num_companies", 10))
            
            if not api_key:
                messages.error(request, "API key is required")
                return render(request, 'linkedin_scraper.html', context)
            
            # Initialize variables
            all_data = []
            
            # Step 1: Fetch tech companies
            url = f"https://api.scrapingdog.com/linkedin/search?api_key={api_key}&query={company_query}"
            response = requests.get(url)
            
            if response.status_code != 200:
                messages.error(request, f"Error fetching companies: {response.status_code}")
                return render(request, 'linkedin_scraper.html', context)
                
            results = response.json()
            companies = [company["name"] for company in results[:num_companies] if "name" in company]
            
            # Step 2: Find HR profiles for each company
            for company in companies:
                hr_url = f"https://api.scrapingdog.com/linkedin/search?api_key={api_key}&query={company}+HR"
                hr_response = requests.get(hr_url)
                
                if hr_response.status_code == 200:
                    profiles = hr_response.json()
                    
                    # Step 3: Fetch profile details
                    for profile in profiles:
                        profile_url = profile.get("linkedin_url")
                        
                        if profile_url:
                            details_url = f"https://api.scrapingdog.com/linkedin/profile?api_key={api_key}&url={profile_url}"
                            details_response = requests.get(details_url)
                            
                            if details_response.status_code == 200:
                                details = details_response.json()
                                details["company"] = company  # Add company name
                                all_data.append(details)
                                
                            time.sleep(1)  # Avoid rate limits
                
                time.sleep(2)  # Avoid rate limits between companies
            
            # Ensure directory exists for saving files
            media_dir = os.path.join('media', 'excel')
            os.makedirs(media_dir, exist_ok=True)
            
            # Generate filename with timestamp
            filename = f"hr_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = os.path.join(media_dir, filename)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(all_data)
            df.to_csv(file_path, index=False)
            
            # Create Excel model entry with the correct path
            excel_record = Excel.objects.create(file=f"excel/{filename}")
            
            # Add results to context for display
            context['profile_count'] = len(all_data)
            context['company_count'] = len(companies)
            context['file_saved'] = True
            context['excel_id'] = excel_record.id
            context['file_path'] = os.path.join('excel', filename)
            
            messages.success(request, f"Successfully scraped {len(all_data)} HR profiles from {len(companies)} companies")
            
        except Exception as e:
            messages.error(request, f"Error during scraping: {str(e)}")
            context['error'] = str(e)
    
    return render(request, 'linkedin_scraper.html', context)

def allScraps(request):
    files = Excel.objects.all()  # Fetch scraped files
    print(files)
    return render(request, 'allscrap.html', {'files':files})



def view_csv_data(request, excel_id):
    try:
        # Get the Excel object by id
        excel_file = Excel.objects.get(id=excel_id)
        
        # Get the file path
        file_path = os.path.join(settings.MEDIA_ROOT, str(excel_file.file))
        
        # Read the CSV using pandas
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            # Get headers
            headers = df.columns.tolist()
            
            # Search functionality
            search_query = request.GET.get('search', '')
            if search_query:
                filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
                df_to_display = filtered_df
            else:
                df_to_display = df
            
            # Convert dataframe to list of lists (not dictionaries)
            # This ensures column order is preserved
            rows = df_to_display.values.tolist()
            
            # Pagination
            page_number = request.GET.get('page', 1)
            paginator = Paginator(rows, 25)  # Show 25 rows per page
            page_obj = paginator.get_page(page_number)
            
            context = {
                'file': excel_file,
                'headers': headers,
                'page_obj': page_obj,
                'row_count': len(rows),
                'total_unfiltered': len(df),
                'search_query': search_query,
            }
            
            return render(request, 'csv_data.html', context)
        else:
            messages.error(request, "CSV file not found on server")
            return redirect('allscraps')
    
    except Excel.DoesNotExist:
        messages.error(request, "File record not found")
        return redirect('allscraps')
    except Exception as e:
        messages.error(request, f"Error reading CSV: {str(e)} || 0 job listing")
        return redirect('allscraps')