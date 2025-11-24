import pdfplumber
import pytesseract
from PIL import Image
import openai
import json
from django.conf import settings
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.core.files.base import ContentFile
from typing import Dict, Any
import os


class DocumentService:
    """
    Service for document processing including OCR, AI extraction, and PO generation.
    
    Handles:
    - Text extraction from PDFs and images
    - AI-based metadata extraction from proforma invoices
    - Purchase order generation
    - Receipt validation against purchase orders
    """
    
    @staticmethod
    def extract_text_from_file(file) -> str:
        """
        Extract text from PDF or image files using OCR.
        
        Args:
            file: Django File object (PDF or image)
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file format is not supported
        """
        # Get file extension
        file_name = file.name if hasattr(file, 'name') else 'unknown.pdf'
        file_ext = file_name.split('.')[-1].lower()
        
        # Reset file pointer to beginning
        file.seek(0)
        
        try:
            if file_ext == 'pdf':
                # Extract text from PDF
                with pdfplumber.open(file) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    text = '\n'.join(text_parts)
                    
            elif file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff']:
                # Extract text from image using OCR
                image = Image.open(file)
                text = pytesseract.image_to_string(image)
                
            else:
                raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: PDF, JPG, PNG")
            
            return text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from file: {str(e)}")
    
    @staticmethod
    def extract_proforma_data(proforma_file) -> Dict[str, Any]:
        """
        Extract structured metadata from proforma invoice using OpenAI.
        
        Args:
            proforma_file: Proforma invoice file (PDF or image)
            
        Returns:
            dict: Extracted metadata including vendor info, items, amounts, etc.
            
        Raises:
            ValueError: If extraction fails or API key is not configured
        """
        if not settings.OPENAI_API_KEY:
            return {
                'error': 'OpenAI API key not configured',
                'vendor_name': 'Unknown',
                'items': [],
                'total_amount': 0,
                'currency': 'USD'
            }
        
        try:
            # Extract text from the document
            text = DocumentService.extract_text_from_file(proforma_file)
            
            if not text:
                return {
                    'error': 'No text could be extracted from document',
                    'vendor_name': 'Unknown',
                    'items': [],
                    'total_amount': 0,
                    'currency': 'USD'
                }
            
            # Use OpenAI to extract structured data
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract structured data from this proforma invoice. 
                        Return JSON with these exact fields:
                        - vendor_name: string
                        - vendor_email: string (or empty if not found)
                        - vendor_phone: string (or empty if not found)
                        - vendor_address: string (or empty if not found)
                        - items: array of objects with {name, quantity, unit_price, total}
                        - subtotal: number
                        - tax: number (or 0 if not found)
                        - total_amount: number
                        - currency: string (USD, EUR, etc.)
                        - invoice_number: string (or empty if not found)
                        - invoice_date: string in YYYY-MM-DD format (or empty if not found)
                        - payment_terms: string (or empty if not found)
                        - delivery_date: string in YYYY-MM-DD format (or empty if not found)
                        
                        If any field cannot be determined, use empty string or 0 for numbers."""
                    },
                    {
                        "role": "user",
                        "content": text[:8000]  # Limit text length for API
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            metadata = json.loads(response.choices[0].message.content)
            return metadata
            
        except Exception as e:
            return {
                'error': f'Extraction failed: {str(e)}',
                'vendor_name': 'Unknown',
                'items': [],
                'total_amount': 0,
                'currency': 'USD'
            }
    
    @staticmethod
    def generate_purchase_order(purchase_request) -> None:
        """
        Generate a PDF purchase order document from an approved request.
        
        Args:
            purchase_request: PurchaseRequest instance to generate PO for
            
        Raises:
            ValueError: If PO generation fails
        """
        try:
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Header
            p.setFont("Helvetica-Bold", 24)
            p.drawString(1*inch, height - 1*inch, "PURCHASE ORDER")
            
            # PO Details
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1*inch, height - 1.5*inch, f"PO Number:")
            p.setFont("Helvetica", 12)
            p.drawString(2.5*inch, height - 1.5*inch, f"PO-{str(purchase_request.id)[:8].upper()}")
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1*inch, height - 1.8*inch, f"Date:")
            p.setFont("Helvetica", 12)
            p.drawString(2.5*inch, height - 1.8*inch, purchase_request.created_at.strftime('%Y-%m-%d'))
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(1*inch, height - 2.1*inch, f"Requested By:")
            p.setFont("Helvetica", 12)
            p.drawString(2.5*inch, height - 2.1*inch, purchase_request.created_by.get_full_name() or purchase_request.created_by.username)
            
            # Vendor Information
            vendor_name = purchase_request.proforma_metadata.get('vendor_name', 'N/A')
            vendor_email = purchase_request.proforma_metadata.get('vendor_email', 'N/A')
            vendor_address = purchase_request.proforma_metadata.get('vendor_address', 'N/A')
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(1*inch, height - 2.8*inch, "Vendor Information:")
            
            p.setFont("Helvetica", 11)
            p.drawString(1*inch, height - 3.1*inch, f"Name: {vendor_name}")
            p.drawString(1*inch, height - 3.4*inch, f"Email: {vendor_email}")
            p.drawString(1*inch, height - 3.7*inch, f"Address: {vendor_address[:60]}")
            
            # Items Table Header
            y_position = height - 4.5*inch
            p.setFont("Helvetica-Bold", 11)
            p.drawString(1*inch, y_position, "Item Description")
            p.drawString(4*inch, y_position, "Quantity")
            p.drawString(5*inch, y_position, "Unit Price")
            p.drawString(6.5*inch, y_position, "Total")
            
            # Draw line under header
            y_position -= 0.1*inch
            p.line(1*inch, y_position, 7.5*inch, y_position)
            
            # Items
            y_position -= 0.3*inch
            p.setFont("Helvetica", 10)
            items = purchase_request.proforma_metadata.get('items', [])
            
            if not items:
                # If no items extracted, show general description
                p.drawString(1*inch, y_position, purchase_request.title[:40])
                p.drawString(4*inch, y_position, "1")
                p.drawString(5*inch, y_position, f"${purchase_request.amount}")
                p.drawString(6.5*inch, y_position, f"${purchase_request.amount}")
                y_position -= 0.3*inch
            else:
                for item in items[:15]:  # Limit to 15 items per page
                    item_name = str(item.get('name', 'Item'))[:35]
                    quantity = item.get('quantity', 1)
                    unit_price = item.get('unit_price', 0)
                    total = item.get('total', quantity * unit_price)
                    
                    p.drawString(1*inch, y_position, item_name)
                    p.drawString(4*inch, y_position, str(quantity))
                    p.drawString(5*inch, y_position, f"${unit_price:.2f}")
                    p.drawString(6.5*inch, y_position, f"${total:.2f}")
                    y_position -= 0.3*inch
                    
                    if y_position < 2*inch:
                        break
            
            # Total
            y_position -= 0.3*inch
            p.line(1*inch, y_position, 7.5*inch, y_position)
            y_position -= 0.3*inch
            
            p.setFont("Helvetica-Bold", 12)
            currency = purchase_request.proforma_metadata.get('currency', 'USD')
            p.drawString(5.5*inch, y_position, f"Total Amount:")
            p.drawString(6.5*inch, y_position, f"{currency} {purchase_request.amount}")
            
            # Footer
            p.setFont("Helvetica-Oblique", 9)
            p.drawString(1*inch, 1*inch, "This is an automatically generated purchase order.")
            p.drawString(1*inch, 0.8*inch, f"Payment Terms: {purchase_request.proforma_metadata.get('payment_terms', 'As agreed')}")
            
            # Finalize PDF
            p.showPage()
            p.save()
            
            # Save to model
            buffer.seek(0)
            purchase_request.purchase_order.save(
                f'PO-{str(purchase_request.id)[:8]}.pdf',
                ContentFile(buffer.read()),
                save=True
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate purchase order: {str(e)}")
    
    @staticmethod
    def validate_receipt(purchase_request, receipt_file) -> Dict[str, Any]:
        """
        Validate receipt against purchase order using AI.
        
        Args:
            purchase_request: PurchaseRequest with PO to validate against
            receipt_file: Receipt file to validate
            
        Returns:
            dict: Validation results with discrepancies and match status
        """
        if not settings.OPENAI_API_KEY:
            return {
                'is_valid': None,
                'error': 'OpenAI API key not configured',
                'discrepancies': [],
                'matched_items': [],
                'total_match': False
            }
        
        try:
            # Extract text from receipt
            receipt_text = DocumentService.extract_text_from_file(receipt_file)
            po_metadata = purchase_request.proforma_metadata
            
            if not receipt_text:
                return {
                    'is_valid': False,
                    'error': 'Could not extract text from receipt',
                    'discrepancies': ['Failed to read receipt'],
                    'matched_items': [],
                    'total_match': False
                }
            
            # Use OpenAI to validate
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = f"""
            Compare this receipt with the expected purchase order data and validate it.
            
            Expected PO data:
            {json.dumps(po_metadata, indent=2)}
            
            Receipt text:
            {receipt_text[:6000]}
            
            Return JSON with:
            - is_valid: boolean (true if receipt matches PO within reasonable tolerance)
            - discrepancies: array of strings describing any issues found
            - matched_items: array of items that matched successfully
            - total_match: boolean (does the total amount match within 5%?)
            - confidence: number 0-100 indicating confidence in validation
            - notes: string with additional observations
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a receipt validation assistant. Compare receipts with purchase orders and identify any discrepancies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            validation = json.loads(response.choices[0].message.content)
            return validation
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'Validation failed: {str(e)}',
                'discrepancies': [str(e)],
                'matched_items': [],
                'total_match': False
            }



