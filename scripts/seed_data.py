import os
import sys
from pathlib import Path
from datetime import datetime, time, date, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django
django.setup()

from django.utils import timezone
from apps.accounts.models import User, UserProfile
from apps.events.models import Event, EventStory
from apps.schedule.models import Speaker, Session, SessionResource
from apps.tickets.models import Ticket
from apps.announcements.models import Announcement, AnnouncementAttachment
from apps.resources.models import Resource
from apps.message_team.models import TeamMember, Conversation, ChatMessage
from apps.content_settings.models import LegalDocument, FAQ


def seed():
    print("🌱 Starting RealSuccess Database Seeding...")

    # 1. Admin & Test Users
    admin_user, created = User.objects.get_or_create(
        email="admin@realsuccess.com",
        defaults={
            "first_name": "Aminul",
            "last_name": "Arnob",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
    )
    if created:
        admin_user.set_password("Admin12345!")
        admin_user.save()
        prof, _ = UserProfile.objects.get_or_create(user=admin_user)
        prof.phone_number = "+1 800 555 0199"
        prof.country = "United States"
        prof.city = "New York"
        prof.save()
        print("✅ Created Admin User: admin@realsuccess.com / Admin12345!")

    attendee_user, created = User.objects.get_or_create(
        email="attendee@realsuccess.com",
        defaults={
            "first_name": "Alex",
            "last_name": "Rivera",
            "is_staff": False,
            "is_superuser": False,
            "is_active": True,
        }
    )
    if created:
        attendee_user.set_password("Attendee12345!")
        attendee_user.save()
        prof, _ = UserProfile.objects.get_or_create(user=attendee_user)
        prof.phone_number = "+1 555 234 5678"
        prof.country = "United States"
        prof.city = "San Francisco"
        prof.save()
        print("✅ Created Attendee User: attendee@realsuccess.com / Attendee12345!")

    # 2. Main Event (Real Success Summit 2026)
    start_d = date.today() + timedelta(days=14)
    end_d = start_d + timedelta(days=2)

    event, _ = Event.objects.get_or_create(
        access_code="RS-AUG-2026-001",
        defaults={
            "name": "Real Success Summit 2026",
            "description": "The premier global conference for real estate mastery, visionary investment strategies, and high-impact capital scaling.",
            "venue": "Suntec Singapore Convention & Exhibition Centre",
            "start_date": start_d,
            "end_date": end_d,
            "days_duration": 3,
            "total_tickets": 1200,
            "status": "Active",
            "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=RS-AUG-2026-001",
        }
    )
    print(f"✅ Created/Verified Event: {event.name} (Code: {event.access_code})")

    # Event Stories
    stories_data = [
        {"title": "Keynote Reveal", "duration": "1:45", "order": 1},
        {"title": "VIP Networking", "duration": "2:10", "order": 2},
        {"title": "Suntec Venue Tour", "duration": "3:00", "order": 3},
    ]
    for s in stories_data:
        EventStory.objects.get_or_create(
            event=event,
            title=s["title"],
            defaults={"duration": s["duration"], "order": s["order"]}
        )

    # 3. Speakers
    spk1, _ = Speaker.objects.get_or_create(
        name="Dr. Joe Arias",
        defaults={
            "role": "Keynote Speaker & Real Estate Visionary",
            "company_name": "RealSuccess Worldwide",
            "bio": "Dr. Joe Arias is a renowned investor, founder of RealSuccess, and author who has transformed thousands of investors globally.",
            "areas_of_expertise": ["Real Estate Investing", "Wealth Building", "Market Scaling"],
            "years_of_experience": "20+ years",
            "workshops_conducted": "250+ Conducted",
            "specialization": "Commercial & Syndication",
            "industry": "Real Estate Capital",
            "is_keynote_spotlight": True,
        }
    )

    spk2, _ = Speaker.objects.get_or_create(
        name="Sarah Jenkins",
        defaults={
            "role": "Managing Director",
            "company_name": "Apex Property Ventures",
            "bio": "Specializing in commercial syndications, fund structure optimization, and tax-advantaged real estate portfolios.",
            "areas_of_expertise": ["Commercial Real Estate", "Syndication", "Private Equity"],
            "years_of_experience": "15+ years",
            "workshops_conducted": "80+ Conducted",
            "specialization": "Fund Structuring",
            "industry": "Private Equity",
            "is_keynote_spotlight": False,
        }
    )

    spk3, _ = Speaker.objects.get_or_create(
        name="Marcus Vance",
        defaults={
            "role": "PropTech & AI Strategist",
            "company_name": "Civic Capital",
            "bio": "Leading authority on AI-powered deal evaluation, automated underwriting, and digital real estate assets.",
            "areas_of_expertise": ["PropTech", "AI Real Estate", "Automated Valuation"],
            "years_of_experience": "12+ years",
            "workshops_conducted": "60+ Conducted",
            "specialization": "PropTech & Tokenization",
            "industry": "FinTech / PropTech",
            "is_keynote_spotlight": True,
        }
    )
    print("✅ Created Speakers: Dr. Joe Arias, Sarah Jenkins, Marcus Vance")

    # 4. Sessions
    sessions_data = [
        {
            "session_title": "Opening Keynote: The Unstoppable Real Estate Blueprint",
            "description": "Discover macroeconomic market shifts and proven acquisition models to thrive in the 2026 property market.",
            "day_number": 1,
            "date": start_d,
            "type": "Keynote",
            "time": "09:30 AM – 11:00 AM",
            "start_time": time(9, 30),
            "end_time": time(11, 0),
            "venue": "Grand Ballroom A",
            "duration": "90 Minutes",
            "speaker": spk1,
            "important_notes": ["Please arrive 15 minutes before start", "Priority front-row seating for VIP badge holders"],
        },
        {
            "session_title": "Hands-On Workshop: Multi-Family Underwriting & Deal Stress-Testing",
            "description": "Live walkthrough analyzing actual deal models, debt structuring, and exit strategies.",
            "day_number": 1,
            "date": start_d,
            "type": "Workshop",
            "time": "11:30 AM – 01:00 PM",
            "start_time": time(11, 30),
            "end_time": time(13, 0),
            "venue": "Executive Room 3B",
            "duration": "90 Minutes",
            "speaker": spk2,
            "important_notes": ["Laptops recommended for spreadsheet model interaction", "Digital model files available under Resources tab"],
        },
        {
            "session_title": "Panel: The Future of PropTech, Tokenization & AI Valuations",
            "description": "Interactive panel featuring leading technology and capital innovators.",
            "day_number": 1,
            "date": start_d,
            "type": "Panel",
            "time": "02:30 PM – 04:00 PM",
            "start_time": time(14, 30),
            "end_time": time(16, 0),
            "venue": "Auditorium West",
            "duration": "90 Minutes",
            "speaker": spk3,
            "important_notes": ["Interactive Q&A via mobile app live chat"],
        },
        {
            "session_title": "VIP Executive Networking & Cocktail Reception",
            "description": "Private lounge access for VIP ticket holders, keynotes, and institutional partners.",
            "day_number": 1,
            "date": start_d,
            "type": "Networking",
            "time": "05:00 PM – 07:30 PM",
            "start_time": time(17, 0),
            "end_time": time(19, 30),
            "venue": "Skyline Lounge, Level 4",
            "duration": "150 Minutes",
            "speaker": spk1,
            "important_notes": ["VIP badge scanning required at entrance", "Complimentary refreshments and hors d'oeuvres provided"],
        },
    ]

    for s_info in sessions_data:
        sess, _ = Session.objects.get_or_create(
            event=event,
            session_title=s_info["session_title"],
            defaults=s_info
        )
        # Add a session resource
        SessionResource.objects.get_or_create(
            session=sess,
            title=f"{sess.session_title} - Handout",
            defaults={
                "file_size": "4.2 MB",
                "file_type": "PDF",
            }
        )
    print("✅ Created Schedule Sessions with Resources")

    # 5. Tickets & Attendees
    ticket, _ = Ticket.objects.get_or_create(
        ticket_id="RS-2026-004582",
        defaults={
            "event": event,
            "user": attendee_user,
            "attendee_name": "Alex Rivera",
            "attendee_email": attendee_user.email,
            "attendee_phone": "+1 555 234 5678",
            "ticket_type": "VIP",
            "price": "$1,000",
            "seat_no": "Row A - Seat 14",
            "check_in_status": "Not Checked In",
            "check_in_time_slot": "08:00 AM",
            "access_code": event.access_code,
            "qr_code_data": f"REALSUCCESS:TICKET:RS-2026-004582:VIP:{event.access_code}",
        }
    )

    Ticket.objects.get_or_create(
        ticket_id="RS-2026-000001",
        defaults={
            "event": event,
            "user": admin_user,
            "attendee_name": "Aminul Arnob",
            "attendee_email": admin_user.email,
            "ticket_type": "VIP",
            "price": "$1,000",
            "seat_no": "VIP Suite 01",
            "check_in_status": "Checked In",
            "checked_in_at": timezone.now(),
            "check_in_time_slot": "08:00 AM",
            "access_code": event.access_code,
            "qr_code_data": f"REALSUCCESS:TICKET:RS-2026-000001:VIP:{event.access_code}",
        }
    )
    print(f"✅ Created Tickets (Sample VIP: {ticket.ticket_id})")

    # 6. Announcements
    Announcement.objects.get_or_create(
        event=event,
        title="Welcome to Real Success Summit 2026!",
        defaults={
            "content": "Registration desks are now open at Level 3. Please have your digital QR badge ready on the RealSuccess mobile app for contactless check-in.",
            "priority": "High Priority",
            "category": "General",
            "takeaway_time": "Time: 8:00 AM → 9:00 AM",
            "takeaway_venue": "Venue: Level 3 Foyer",
            "published_by": "RealSuccess Event Team",
            "reading_time": "1 min read",
            "is_new": True,
        }
    )
    Announcement.objects.get_or_create(
        event=event,
        title="VIP Executive Lounge Access Pass",
        defaults={
            "content": "VIP badge holders can enjoy complimentary refreshments, private meeting suites, and priority seating in Skyline Lounge.",
            "priority": "Important",
            "category": "VIP Access",
            "takeaway_time": "All Day Access",
            "takeaway_venue": "Skyline Lounge Level 4",
            "published_by": "VIP Concierge",
            "reading_time": "2 min read",
            "is_new": False,
        }
    )
    print("✅ Created Announcements")

    # 7. Resources
    Resource.objects.get_or_create(
        event=event,
        title="Real Success 2026 Official Playbook",
        defaults={
            "description": "Comprehensive strategic guide covering underwriting, capital raising, and property scaling.",
            "category": "Guides",
            "type": "PDF",
            "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "file_size": "14.2 MB",
            "is_featured": True,
            "download_count": 542,
        }
    )
    Resource.objects.get_or_create(
        event=event,
        title="Multi-Family Financial Underwriting Model",
        defaults={
            "description": "Standardized dynamic Excel model for syndication stress-testing and waterfall distributions.",
            "category": "Document",
            "type": "Document",
            "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "file_size": "3.8 MB",
            "is_featured": False,
            "download_count": 320,
        }
    )
    Resource.objects.get_or_create(
        event=event,
        title="Keynote Slide Deck: Scaling Wealth in 2026",
        defaults={
            "description": "Full presentation deck presented by Dr. Joe Arias.",
            "category": "PDF",
            "type": "PDF",
            "file_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "file_size": "28.5 MB",
            "is_featured": True,
            "download_count": 418,
        }
    )
    print("✅ Created Resources")

    # 8. Team Members & Chat
    tm1, _ = TeamMember.objects.get_or_create(
        email="elena.r@realsuccess.com",
        defaults={
            "name": "Elena Rodriguez",
            "display_name": "Elena R.",
            "role": "Lead Event Coordinator",
            "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80",
            "online": True,
            "channel_type": "direct-staff",
            "event": event,
        }
    )

    tm2, _ = TeamMember.objects.get_or_create(
        email="concierge@realsuccess.com",
        defaults={
            "name": "VIP Concierge Desk",
            "display_name": "VIP Concierge",
            "role": "VIP Services & Logistics",
            "avatar": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&auto=format&fit=crop&q=80",
            "online": True,
            "channel_type": "event-group",
            "event": event,
        }
    )

    conv, _ = Conversation.objects.get_or_create(
        team_member=tm1,
        user=attendee_user,
        defaults={"channel_type": "direct-staff", "event": event}
    )
    ChatMessage.objects.get_or_create(
        conversation=conv,
        text="Hi Alex! Welcome to Real Success Summit 2026. Let us know if you need assistance with your badge or sessions.",
        defaults={
            "sender_staff": tm1,
            "sender_name": tm1.display_name,
            "is_sender": True,
            "is_read": True,
        }
    )
    print("✅ Created Team Members & Concierge Chat")

    # 9. Legal Document & FAQs
    LegalDocument.objects.get_or_create(
        title="RealSuccess Legal Settings",
        defaults={
            "privacy_policy_content": (
                "<h2>Privacy Policy</h2>"
                "<p>RealSuccess is committed to safeguarding the personal information of our attendees and members. "
                "We collect registration credentials, badge scanning logs, and communication data strictly to deliver event services.</p>"
                "<h3>1. Information We Collect</h3>"
                "<p>Names, corporate titles, contact phone, email, and conference check-in timestamps.</p>"
            ),
            "terms_conditions_content": (
                "<h2>Terms & Conditions</h2>"
                "<p>By registering or using the RealSuccess application and accessing our summit venues, you agree to comply with our event conduct policies.</p>"
                "<h3>1. Badge & Access Rules</h3>"
                "<p>Access passes are non-transferable without written consent from event organizers.</p>"
            ),
        }
    )

    faqs = [
        ("How do I check in with my ticket?", "Simply open the 'Ticket' tab in the app to display your dynamic QR code at the entrance turnstiles.", "registration", 1),
        ("Where can I find WiFi access details?", "High-speed complimentary WiFi is available across the venue. Connect to 'RealSuccess_Guest' (no password required).", "venue", 2),
        ("Are presentation slides available for download?", "Yes! Head to the 'Resources' tab or visit any individual session page to download PDFs and spreadsheets directly.", "general", 3),
        ("What perks are included with VIP tickets?", "VIP tickets include front-row reserved seating, dedicated concierge support, and exclusive access to the Level 4 Skyline Lounge.", "vip", 4),
    ]
    for q, a, cat, ord_num in faqs:
        FAQ.objects.get_or_create(
            question=q,
            defaults={"answer": a, "category": cat, "order": ord_num, "is_active": True}
        )
    print("✅ Created Legal Documents and FAQs")

    print("\n🎉 Database Seeding Completed Successfully! All models ready.")


if __name__ == "__main__":
    seed()
