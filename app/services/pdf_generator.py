from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime

class PDFGenerator:
    
    @staticmethod
    def generate_booking_invoice(booking):
        """Generate PDF invoice for a booking (receipt)"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        story.append(Paragraph("Service Booking Invoice", title_style))
        
        # Invoice info
        info_style = styles['Normal']
        story.append(Paragraph(f"Invoice ID: INV-{booking.id:06d}", info_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Customer Info
        story.append(Paragraph("<b>Customer Information</b>", styles['Heading2']))
        customer_name = booking.customer.full_name if booking.customer else 'N/A'
        customer_email = booking.customer.email if booking.customer else 'N/A'
        customer_phone = booking.customer.phone if booking.customer and booking.customer.phone else 'N/A'
        
        story.append(Paragraph(f"Name: {customer_name}", info_style))
        story.append(Paragraph(f"Email: {customer_email}", info_style))
        story.append(Paragraph(f"Phone: {customer_phone}", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Service Details
        story.append(Paragraph("<b>Service Details</b>", styles['Heading2']))
        service_name = booking.service.name if booking.service else 'N/A'
        provider_name = booking.provider.full_name if booking.provider else 'N/A'
        schedule_time = booking.schedule.start_time.strftime('%Y-%m-%d %H:%M') if booking.schedule else 'N/A'
        
        story.append(Paragraph(f"Service: {service_name}", info_style))
        story.append(Paragraph(f"Provider: {provider_name}", info_style))
        story.append(Paragraph(f"Date & Time: {schedule_time}", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Payment Table
        data = [
            ['Description', 'Amount'],
            ['Service Fee', f'${booking.total_price:.2f}'],
            ['Total', f'${booking.total_price:.2f}']
        ]
        
        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Payment Status - اصلاح شده
        if booking.payment_status == 'paid':
            status_color = colors.green
            status_text = "PAID"
        else:
            status_color = colors.red
            status_text = "UNPAID"
        
        story.append(Paragraph(f"Payment Status: <font color='{status_color}'>{status_text}</font>", info_style))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER)
        story.append(Paragraph("Thank you for choosing ServiceHub!", footer_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_customer_bookings_report(bookings, customer):
        """Generate report of customer bookings"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("Customer Bookings Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report Info
        info_style = styles['Normal']
        story.append(Paragraph(f"Customer Name: {customer.full_name}", info_style))
        story.append(Paragraph(f"Customer Email: {customer.email}", info_style))
        story.append(Paragraph(f"Customer Phone: {customer.phone or 'N/A'}", info_style))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        total_bookings = len(bookings)
        total_spent = sum(b.total_price for b in bookings if b.payment_status == 'paid')
        completed_count = sum(1 for b in bookings if b.status == 'completed')
        
        story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
        story.append(Paragraph(f"Total Bookings: {total_bookings}", info_style))
        story.append(Paragraph(f"Total Spent: ${total_spent:.2f}", info_style))
        story.append(Paragraph(f"Completed Services: {completed_count}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Bookings Table
        data = [['ID', 'Service', 'Provider', 'Date', 'Amount', 'Status', 'Payment']]
        for booking in bookings:
            service_name = booking.service.name if booking.service else 'N/A'
            provider_name = booking.provider.full_name if booking.provider else 'N/A'
            booking_date = booking.schedule.start_time.strftime('%Y-%m-%d %H:%M') if booking.schedule else 'N/A'
            
            data.append([
                str(booking.id),
                service_name[:30],
                provider_name[:25],
                booking_date,
                f'${booking.total_price:.2f}',
                booking.status.value,
                booking.payment_status.value
            ])
        
        table = Table(data, colWidths=[0.6*inch, 1.8*inch, 1.5*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_provider_bookings_report(bookings, provider):
        """Generate report of provider bookings"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("Provider Bookings Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report Info
        info_style = styles['Normal']
        story.append(Paragraph(f"Provider Name: {provider.full_name}", info_style))
        story.append(Paragraph(f"Provider Email: {provider.email}", info_style))
        story.append(Paragraph(f"Provider Phone: {provider.phone or 'N/A'}", info_style))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary
        total_bookings = len(bookings)
        total_revenue = sum(b.total_price for b in bookings if b.payment_status == 'paid')
        pending_count = sum(1 for b in bookings if b.status == 'pending')
        confirmed_count = sum(1 for b in bookings if b.status == 'confirmed')
        
        story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
        story.append(Paragraph(f"Total Bookings: {total_bookings}", info_style))
        story.append(Paragraph(f"Total Revenue: ${total_revenue:.2f}", info_style))
        story.append(Paragraph(f"Pending Approvals: {pending_count}", info_style))
        story.append(Paragraph(f"Confirmed Bookings: {confirmed_count}", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Bookings Table
        data = [['ID', 'Customer', 'Service', 'Date', 'Amount', 'Status', 'Payment']]
        for booking in bookings:
            customer_name = booking.customer.full_name if booking.customer else 'N/A'
            service_name = booking.service.name if booking.service else 'N/A'
            booking_date = booking.schedule.start_time.strftime('%Y-%m-%d %H:%M') if booking.schedule else 'N/A'
            
            data.append([
                str(booking.id),
                customer_name[:25],
                service_name[:30],
                booking_date,
                f'${booking.total_price:.2f}',
                booking.status.value,
                booking.payment_status.value
            ])
        
        table = Table(data, colWidths=[0.6*inch, 1.5*inch, 1.8*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generate_admin_stats_report(stats, bookings, users, services):
        """Generate detailed admin statistics report"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=15,
            spaceAfter=10
        )
        
        # Title
        story.append(Paragraph("System Administration Report", title_style))
        story.append(Spacer(1, 0.1*inch))
        
        # Report Info
        info_style = styles['Normal']
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        story.append(Paragraph(f"<b>Report Period:</b> All time", info_style))
        story.append(Spacer(1, 0.3*inch))
        
        # ========== 1. USER STATISTICS ==========
        story.append(Paragraph("1. USER STATISTICS", subtitle_style))
        
        # User stats table
        user_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total Users', str(stats['users']['total']), '100%'],
            ['Customers', str(stats['users']['customers']), f"{(stats['users']['customers']/stats['users']['total']*100):.1f}%" if stats['users']['total'] > 0 else '0%'],
            ['Providers', str(stats['users']['providers']), f"{(stats['users']['providers']/stats['users']['total']*100):.1f}%" if stats['users']['total'] > 0 else '0%']
        ]
        
        # Active vs Inactive users
        active_users = sum(1 for u in users if u.is_active)
        inactive_users = stats['users']['total'] - active_users
        
        user_data.extend([
            ['Active Users', str(active_users), f"{(active_users/stats['users']['total']*100):.1f}%" if stats['users']['total'] > 0 else '0%'],
            ['Inactive Users', str(inactive_users), f"{(inactive_users/stats['users']['total']*100):.1f}%" if stats['users']['total'] > 0 else '0%']
        ])
        
        user_table = Table(user_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        user_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(user_table)
        story.append(Spacer(1, 0.2*inch))
        
        # ========== 2. SERVICE STATISTICS ==========
        story.append(Paragraph("2. SERVICE STATISTICS", subtitle_style))
        
        service_data = [
            ['Metric', 'Count', 'Percentage'],
            ['Total Services', str(stats['services']['total']), '100%'],
            ['Active Services', str(stats['services']['active']), f"{(stats['services']['active']/stats['services']['total']*100):.1f}%" if stats['services']['total'] > 0 else '0%'],
            ['Inactive Services', str(stats['services']['inactive']), f"{(stats['services']['inactive']/stats['services']['total']*100):.1f}%" if stats['services']['total'] > 0 else '0%']
        ]
        
        # Category distribution
        from collections import Counter
        categories = [s.category for s in services if s.category]
        category_counts = Counter(categories)
        
        service_table = Table(service_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(service_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Category distribution table
        if category_counts:
            story.append(Paragraph("<b>Services by Category:</b>", info_style))
            cat_data = [['Category', 'Count', 'Percentage']]
            for cat, count in category_counts.most_common():
                cat_data.append([cat, str(count), f"{(count/len(services)*100):.1f}%"])
            
            cat_table = Table(cat_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(cat_table)
            story.append(Spacer(1, 0.2*inch))
        
        # ========== 3. BOOKING STATISTICS ==========
        story.append(Paragraph("3. BOOKING STATISTICS", subtitle_style))
        
        # Booking status distribution
        from collections import Counter
        booking_statuses = [b.status for b in bookings]
        status_counts = Counter(booking_statuses)
        
        booking_data = [
            ['Status', 'Count', 'Percentage'],
            ['Pending', str(status_counts.get('pending', 0)), f"{(status_counts.get('pending', 0)/len(bookings)*100):.1f}%" if bookings else '0%'],
            ['Confirmed', str(status_counts.get('confirmed', 0)), f"{(status_counts.get('confirmed', 0)/len(bookings)*100):.1f}%" if bookings else '0%'],
            ['Completed', str(status_counts.get('completed', 0)), f"{(status_counts.get('completed', 0)/len(bookings)*100):.1f}%" if bookings else '0%'],
            ['Cancelled', str(status_counts.get('cancelled', 0)), f"{(status_counts.get('cancelled', 0)/len(bookings)*100):.1f}%" if bookings else '0%']
        ]
        
        booking_table = Table(booking_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        booking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(booking_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Booking trends (daily/weekly/monthly)
        story.append(Paragraph("<b>Booking Trends:</b>", info_style))
        story.append(Paragraph(f"• Today: {stats['bookings']['today']} bookings", info_style))
        story.append(Paragraph(f"• This Week: {stats['bookings']['weekly']} bookings", info_style))
        
        # Average bookings per day
        if bookings:
            from datetime import timedelta
            first_booking = min(b.created_at for b in bookings if b.created_at)
            last_booking = max(b.created_at for b in bookings if b.created_at)
            days_active = (last_booking - first_booking).days + 1
            avg_per_day = len(bookings) / max(days_active, 1)
            story.append(Paragraph(f"• Average Bookings per Day: {avg_per_day:.1f}", info_style))
        story.append(Spacer(1, 0.1*inch))
        
        # ========== 4. PAYMENT STATISTICS ==========
        story.append(Paragraph("4. PAYMENT STATISTICS", subtitle_style))
        
        # Payment status distribution
        payment_statuses = [b.payment_status for b in bookings]
        payment_counts = Counter(payment_statuses)
        
        payment_data = [
            ['Payment Status', 'Count', 'Total Amount'],
            ['Paid', str(payment_counts.get('paid', 0)), f"${sum(b.total_price for b in bookings if b.payment_status == 'paid'):.2f}"],
            ['Unpaid', str(payment_counts.get('unpaid', 0)), f"${sum(b.total_price for b in bookings if b.payment_status == 'unpaid'):.2f}"],
            ['Refunded', str(payment_counts.get('refunded', 0)), f"${sum(b.total_price for b in bookings if b.payment_status == 'refunded'):.2f}"]
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph(f"<b>Total Revenue:</b> ${stats['revenue']:.2f}", info_style))
        story.append(Paragraph(f"<b>Average Booking Value:</b> ${(stats['revenue']/max(len([b for b in bookings if b.payment_status == 'paid']), 1)):.2f}", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # ========== 5. MOST BOOKED SERVICES ==========
        story.append(Paragraph("5. MOST BOOKED SERVICES", subtitle_style))
        
        if stats.get('most_booked_services'):
            for i, service in enumerate(stats['most_booked_services'], 1):
                story.append(Paragraph(f"{i}. <b>{service['name']}</b> - {service['count']} bookings", info_style))
        else:
            story.append(Paragraph("No data available", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # ========== 6. TOP PROVIDERS ==========
        story.append(Paragraph("6. TOP PROVIDERS (by bookings)", subtitle_style))
        
        from collections import defaultdict
        provider_bookings = defaultdict(int)
        for booking in bookings:
            if booking.provider:
                provider_bookings[booking.provider.full_name] += 1
        
        top_providers = sorted(provider_bookings.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_providers:
            for i, (name, count) in enumerate(top_providers, 1):
                story.append(Paragraph(f"{i}. <b>{name}</b> - {count} bookings", info_style))
        else:
            story.append(Paragraph("No data available", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # ========== 7. TOP CUSTOMERS ==========
        story.append(Paragraph("7. TOP CUSTOMERS (by spending)", subtitle_style))
        
        customer_spending = defaultdict(float)
        for booking in bookings:
            if booking.customer and booking.payment_status == 'paid':
                customer_spending[booking.customer.full_name] += booking.total_price
        
        top_customers = sorted(customer_spending.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if top_customers:
            for i, (name, amount) in enumerate(top_customers, 1):
                story.append(Paragraph(f"{i}. <b>{name}</b> - ${amount:.2f}", info_style))
        else:
            story.append(Paragraph("No data available", info_style))
        story.append(Spacer(1, 0.2*inch))
        
        # ========== 8. RECENT ACTIVITY ==========
        story.append(Paragraph("8. RECENT BOOKINGS (Last 10)", subtitle_style))
        
        recent_bookings = sorted(bookings, key=lambda x: x.created_at, reverse=True)[:10]
        
        if recent_bookings:
            recent_data = [['ID', 'Customer', 'Service', 'Date', 'Amount', 'Status']]
            for b in recent_bookings:
                recent_data.append([
                    str(b.id),
                    (b.customer.full_name if b.customer else 'Unknown')[:20],
                    (b.service.name if b.service else 'Unknown')[:25],
                    b.created_at.strftime('%Y-%m-%d') if b.created_at else 'N/A',
                    f'${b.total_price:.2f}',
                    b.status.value
                ])
            
            recent_table = Table(recent_data, colWidths=[0.5*inch, 1.5*inch, 1.8*inch, 1*inch, 0.8*inch, 0.8*inch])
            recent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(recent_table)
        else:
            story.append(Paragraph("No recent bookings", info_style))
        
        doc.build(story)
        buffer.seek(0)
        return buffer