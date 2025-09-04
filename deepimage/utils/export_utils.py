import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
import tempfile
from django.shortcuts import render

def export_pdf(request, analysis_id):
    """Export analysis as PDF using xhtml2pdf (Windows compatible)"""
    from ..models import ForensicAnalysis
    try:
        analysis = ForensicAnalysis.objects.get(id=analysis_id)
        
        # Render HTML template
        html_string = render_to_string('pdf_report.html', {
            'analysis': analysis,
            'result': analysis.raw_prediction_data,
            'base_url': request.build_absolute_uri('/')
        })
        
        # Create PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="forensic_report_{analysis.report_id}.pdf"'
        
        # Generate PDF
        pdf_status = pisa.CreatePDF(
            html_string,
            dest=response,
            link_callback=link_callback
        )
        
        if pdf_status.err:
            return HttpResponse('PDF generation error', status=500)
            
        return response
        
    except ForensicAnalysis.DoesNotExist:
        return HttpResponse("Report not found", status=404)

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    # Convert data URIs
    if uri.startswith("data:"):
        return uri
        
    # Use static files
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    # Use media files
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    # Use absolute URLs
    elif uri.startswith('http'):
        return uri
    else:
        # Local file path
        path = os.path.join(settings.STATIC_ROOT, uri)
    
    # Make sure the file exists
    if not os.path.isfile(path):
        raise Exception(f'File not found: {path}')
        
    return path

def export_print_view(request, analysis_id):
    """View for print-friendly version"""
    from ..models import ForensicAnalysis
    try:
        analysis = ForensicAnalysis.objects.get(id=analysis_id)
        return render(request, 'print_report.html', {
            'analysis': analysis,
            'result': analysis.raw_prediction_data
        })
    except ForensicAnalysis.DoesNotExist:
        return HttpResponse("Report not found", status=404)