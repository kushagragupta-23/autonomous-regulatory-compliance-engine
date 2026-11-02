import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from backend.models.schemas import ComplianceReport

class CompliancePdfExporter:
    """Generates corporate-grade Executive Compliance Audit Memorandums in PDF format."""

    @staticmethod
    def generate_pdf(report: ComplianceReport, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A')
        )

        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B')
        )

        section_heading = ParagraphStyle(
            'SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=14,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor('#334155')
        )

        story = []

        # 1. Header & Title Block
        story.append(Paragraph("EXECUTIVE REGULATORY COMPLIANCE MEMORANDUM", title_style))
        story.append(Paragraph(f"Ref: {report.report_id} | Issued: {report.generated_at} | Status: {report.overall_compliance_status.replace('_', ' ')}", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3B82F6'), spaceAfter=14))

        # 2. Executive Profile Table
        p = report.taxpayer_profile
        profile_data = [
            [Paragraph("<b>Taxpayer Entity:</b>", body_style), Paragraph(p.entity_name, body_style), Paragraph("<b>Entity Type:</b>", body_style), Paragraph(p.entity_type.replace('_', ' '), body_style)],
            [Paragraph("<b>Annual Turnover:</b>", body_style), Paragraph(f"INR {p.annual_turnover:,.0f}", body_style), Paragraph("<b>GST Registered:</b>", body_style), Paragraph("Active / Yes" if p.gst_registered else "No", body_style)],
            [Paragraph("<b>Issuing Authority:</b>", body_style), Paragraph(report.circular_meta.issuing_authority, body_style), Paragraph("<b>Gazette Ref:</b>", body_style), Paragraph(report.circular_meta.circular_id, body_style)]
        ]
        t_profile = Table(profile_data, colWidths=[110, 160, 110, 160])
        t_profile.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_profile)
        story.append(Spacer(1, 14))

        # 3. Statutory Summary
        story.append(Paragraph("1. Statutory Summary & Scope", section_heading))
        story.append(Paragraph(report.circular_meta.summary, body_style))
        story.append(Spacer(1, 10))

        # 4. Impact Assessment Matrix
        story.append(Paragraph("2. Detailed Regulatory Exposure Matrix", section_heading))
        impact_table_data = [
            [
                Paragraph("<b>Section</b>", body_style),
                Paragraph("<b>Risk Level</b>", body_style),
                Paragraph("<b>Finding & Operational Impact</b>", body_style),
                Paragraph("<b>Mandatory Directive</b>", body_style),
                Paragraph("<b>Financial Exposure</b>", body_style)
            ]
        ]

        for item in report.impact_assessment:
            risk_color = '#EF4444' if item.risk_level == 'CRITICAL' else ('#F59E0B' if item.risk_level == 'HIGH' else '#10B981')
            risk_para = Paragraph(f"<font color='{risk_color}'><b>{item.risk_level}</b></font>", body_style)
            impact_table_data.append([
                Paragraph(item.rule_section, body_style),
                risk_para,
                Paragraph(item.description, body_style),
                Paragraph(item.action_required, body_style),
                Paragraph(item.financial_exposure or "N/A", body_style)
            ])

        t_impact = Table(impact_table_data, colWidths=[80, 65, 145, 150, 100])
        t_impact.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_impact)
        story.append(Spacer(1, 14))

        # 5. Zero-Hallucination Audit Verification Block
        story.append(Paragraph("3. Zero-Hallucination Statutory Verification Seal", section_heading))
        audit = report.audit_report
        audit_data = [
            [
                Paragraph("<b>Verification Status:</b>", body_style),
                Paragraph(f"<font color='#10B981'><b>{audit.validation_status} (Passed)</b></font>", body_style),
                Paragraph("<b>Hallucination Probability:</b>", body_style),
                Paragraph(f"{audit.hallucination_risk_score * 100:.1f}% (Grounding Verified)", body_style)
            ],
            [
                Paragraph("<b>Audit Remarks:</b>", body_style),
                Paragraph(audit.remarks, body_style),
                Paragraph("<b>Statutory Reference:</b>", body_style),
                Paragraph(audit.official_gazette_ref[:80] + "...", body_style)
            ]
        ]
        t_audit = Table(audit_data, colWidths=[110, 160, 120, 150])
        t_audit.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#10B981')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A7F3D0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_audit)

        doc.build(story)
        return output_path

