# vente/utils.py
from django.db import models
from django.conf import settings
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from datetime import datetime

def generate_receipt_pdf(vente):
    """
    Génère un reçu professionnel épuré
    """
    buffer = BytesIO()
    
    # Créer le document avec marges standards
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=0.5*cm,
        bottomMargin=2*cm,
        author=vente.entreprise.nom,
        title=f"Reçu #{vente.id:06d}",
        subject="Reçu de vente"
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # 1. En-tête de l'entreprise - Style épuré
    # Nom de l'entreprise en grand
    nom_style = ParagraphStyle(
        name='NomEntreprise',
        parent=styles['Normal'],
        fontSize=26,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        leading=30
    )
    
    story.append(Paragraph(vente.entreprise.nom.upper(), nom_style))
    
    # IFU - un peu plus grand mais plus petit que le nom
    ifu_style = ParagraphStyle(
        name='IFUStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=4,
        leading=14
    )
    
    story.append(Paragraph(f"{vente.entreprise.ifu}", ifu_style))
    
    # Contact
    if hasattr(vente.entreprise, 'contact') and vente.entreprise.contact:
        contact_style = ParagraphStyle(
            name='ContactStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=10,
            leading=13
        )
        story.append(Paragraph(f"TEL: {vente.entreprise.contact}", contact_style))
    
    # Ligne de séparation fine
    story.append(Paragraph("<hr width='90%'/>", 
                          ParagraphStyle(name='Separator', fontSize=1, alignment=TA_CENTER)))
    story.append(Spacer(1, 15))
    
    # 2. Titre du reçu
    title_style = ParagraphStyle(
        name='ReceiptTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=20
    )
    
    story.append(Paragraph("RECU DE VENTE", title_style))
    
    # 3. Informations de la transaction
    # Style pour les labels
    label_style = ParagraphStyle(
        name='Label',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica',
        spaceAfter=2,
        leading=12
    )
    
    # Style pour les valeurs
    value_style = ParagraphStyle(
        name='Value',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        leading=13
    )
    
    # Informations de base
    info_data = [
        [Paragraph("<b>RÉFÉRENCE:</b>", label_style), 
         Paragraph("<b>DATE:</b>", label_style),
         Paragraph("<b>HEURE:</b>", label_style)],
        [Paragraph(f"#{vente.id:06d}", value_style), 
         Paragraph(vente.date.strftime('%d/%m/%Y'), value_style),
         Paragraph(vente.date.strftime('%H:%M'), value_style)]
    ]
    
    info_table = Table(info_data, colWidths=[6*cm, 5*cm, 5*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # 4. Informations client et vendeur
    # Section client
    client_section = []
    client_section.append(Paragraph("<b>CLIENT</b>", 
                                   ParagraphStyle(name='SectionTitle', fontSize=11, 
                                                 fontName='Helvetica-Bold', spaceAfter=5)))
    client_name = vente.client.nom if vente.client else "COMPTANT"
    client_section.append(Paragraph(client_name, value_style))
    
    if vente.client and vente.client.contact:
        client_section.append(Paragraph(f"TEL: {vente.client.contact}", label_style))
    
    # Section vendeur
    vendeur_section = []
    vendeur_section.append(Paragraph("<b>VENDEUR</b>", 
                                    ParagraphStyle(name='SectionTitle', fontSize=11, 
                                                  fontName='Helvetica-Bold', spaceAfter=5)))
    vendeur_name = vente.utilisateur.get_full_name() or vente.utilisateur.username
    vendeur_section.append(Paragraph(vendeur_name, value_style))
    
    # Tableau client/vendeur
    cv_table_data = [[client_section, vendeur_section]]
    cv_table = Table(cv_table_data, colWidths=[8*cm, 8*cm])
    cv_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    story.append(cv_table)
    story.append(Spacer(1, 25))
    
    # 5. Tableau des produits - Style minimaliste
    lignes = vente.lignes.all()
    
    # Créer les données du tableau
    table_data = []
    
    # En-têtes
    headers = ["PRODUIT", "QTÉ", "PRIX UNITAIRE", "MONTANT"]
    table_data.append(headers)
    
    # Style pour l'en-tête du tableau
    header_style = TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
    ])
    
    # Style pour les lignes de données
    data_style = TableStyle([
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Quantité centrée
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Prix alignés à droite
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ])
    
    # Ajouter les lignes de produits
    for ligne in lignes:
        produit_nom = ligne.produit.nom if ligne.produit else "Article"
        table_data.append([
            Paragraph(produit_nom, 
                     ParagraphStyle(name='Product', fontSize=10, alignment=TA_LEFT)),
            str(ligne.quantite),
            f"{ligne.prix_unitaire:,.0f} FCFA",
            f"{ligne.total:,.0f} FCFA"
        ])
    
    # Créer le tableau
    col_widths = [9*cm, 2*cm, 3.5*cm, 3.5*cm]
    product_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Appliquer les styles
    product_table.setStyle(header_style)
    product_table.setStyle(data_style)
    
    # Ligne de séparation avant le total
    product_table.setStyle(TableStyle([
        ('LINEABOVE', (0, len(table_data)), (-1, len(table_data)), 1, colors.black),
    ]))
    
    story.append(product_table)
    story.append(Spacer(1, 25))
    
    # 6. Section Total
    total_style = ParagraphStyle(
        name='TotalStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.black,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
        spaceAfter=10,
        leading=16
    )
    
    # Tableau pour les totaux
    total_data = [
        ["", "", "TOTAL:", Paragraph(f"{vente.total:,.0f} FCFA", total_style)]
    ]
    
    total_table = Table(total_data, colWidths=[9*cm, 2*cm, 3.5*cm, 3.5*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (2, 0), 12),
        ('VALIGN', (2, 0), (-1, 0), 'MIDDLE'),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 40))
    
    # 7. Espaces de signature - Style épuré
    # Style pour les lignes de signature
    signature_line_style = ParagraphStyle(
        name='SignatureLine',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        leading=10
    )
    
    # Style pour les labels de signature
    signature_label_style = ParagraphStyle(
        name='SignatureLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceBefore=5,
        leading=11
    )
    
    # Espace pour la signature du vendeur
    vendeur_signature = []
    vendeur_signature.append(Spacer(1, 20))
    vendeur_signature.append(Paragraph("_" * 40, signature_line_style))
    vendeur_signature.append(Paragraph("Signature du vendeur", signature_label_style))
    vendeur_signature.append(Paragraph(vendeur_name, 
                                      ParagraphStyle(name='VendeurName', fontSize=9, 
                                                    alignment=TA_CENTER)))
    vendeur_signature.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", 
                                      ParagraphStyle(name='Date', fontSize=8, 
                                                    alignment=TA_CENTER)))
    
    # Espace pour la signature du client
    client_signature = []
    client_signature.append(Spacer(1, 20))
    client_signature.append(Paragraph("_" * 40, signature_line_style))
    client_signature.append(Paragraph("Signature du client", signature_label_style))
    client_signature.append(Paragraph(client_name, 
                                     ParagraphStyle(name='ClientName', fontSize=9, 
                                                   alignment=TA_CENTER)))
    client_signature.append(Paragraph("Lu et approuvé", 
                                     ParagraphStyle(name='Approuve', fontSize=8, 
                                                   alignment=TA_CENTER, 
                                                   fontName='Helvetica-Oblique')))
    
    # Tableau pour les signatures
    signature_data = [[vendeur_signature, client_signature]]
    signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 30))
    
    # 8. Bas de reçu simple
    footer_style = ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceBefore=10,
        leading=10
    )
    
    # Ligne de séparation fine
    story.append(Paragraph("<hr width='100%'/>", 
                          ParagraphStyle(name='FooterLine', fontSize=1, alignment=TA_CENTER)))
    story.append(Spacer(1, 10))
    
    # Texte du bas
    footer_text = (
        f"Document émis par {vente.entreprise.nom} • "
        f"{vente.entreprise.ifu}"
        f"Reçu généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} • "
        f"Conserver ce document pour toute référence"
    )
    
    story.append(Paragraph(footer_text, footer_style))
    
    # Mention finale discrète
    final_mention = ParagraphStyle(
        name='FinalMention',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        spaceBefore=5,
        leading=8
    )
    
    story.append(Paragraph("Merci de votre confiance", final_mention))
    
    # Générer le PDF
    doc.build(story)
    
    # Retourner les bytes du PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def generate_invoice_pdf(vente):
    """
    Génère une facture simple
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=0.5*cm,
        bottomMargin=2*cm,
        author=vente.entreprise.nom,
        title=f"Facture #{vente.id:06d}",
        subject="Facture"
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # En-tête entreprise
    nom_style = ParagraphStyle(
        name='NomEntreprise',
        parent=styles['Normal'],
        fontSize=30,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=8,
        leading=30
    )
    
    story.append(Paragraph(vente.entreprise.nom.upper(), nom_style))
    
    ifu_style = ParagraphStyle(
        name='IFUStyle',
        parent=styles['Normal'],
        fontSize=20,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=4,
        leading=14
    )
    
    story.append(Paragraph(f"{vente.entreprise.ifu}", ifu_style))
    
    if hasattr(vente.entreprise, 'contact') and vente.entreprise.contact:
        contact_style = ParagraphStyle(
            name='ContactStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica',
            spaceAfter=20,
            leading=13
        )
        story.append(Paragraph(f"TEL: {vente.entreprise.contact}", contact_style))
    
    # Ligne de séparation
    story.append(Paragraph("<hr width='90%'/>", 
                          ParagraphStyle(name='Separator', fontSize=1, alignment=TA_CENTER)))
    story.append(Spacer(1, 15))
    
    # Titre FACTURE
    title_style = ParagraphStyle(
        name='InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=20
    )
    
    story.append(Paragraph("FACTURE", title_style))
    
    # Informations facture simples
    info_style = ParagraphStyle(
        name='InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT,
        fontName='Helvetica',
        spaceAfter=5,
        leading=12
    )
    
    story.append(Paragraph(f"<b>Facture N°:</b> #{vente.id:06d}", info_style))
    story.append(Paragraph(f"<b>Date facture:</b> {datetime.now().strftime('%d/%m/%Y')}", info_style))
    story.append(Paragraph(f"<b>Date vente:</b> {vente.date.strftime('%d/%m/%Y %H:%M')}", info_style))
    
    story.append(Spacer(1, 100))
    story.append(Paragraph("Document facture - Structure similaire au reçu", 
                          ParagraphStyle(name='TempText', fontSize=12, alignment=TA_CENTER)))
    
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes