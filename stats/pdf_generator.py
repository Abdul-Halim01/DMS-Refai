from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
import traceback
import tempfile
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pandas as pd


# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Register default fonts - using built-in fonts instead of Roboto
try:
    # Try to register Helvetica if not already registered
    FONT_NAME = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'
    ITALIC_FONT = 'Helvetica-Oblique'
    logger.info("Using Helvetica font family")
except:
    # Fall back to Times-Roman if needed
    FONT_NAME = 'Times-Roman'
    BOLD_FONT = 'Times-Bold'
    ITALIC_FONT = 'Times-Italic'
    logger.warning("Falling back to Times-Roman font family")

# Create a custom header/footer flowable
class HeaderFooter(Flowable):
    """A custom flowable to add headers and footers with page numbers"""
    
    def __init__(self, width, height, report_title, page_type="header"):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.report_title = report_title
        self.page_type = page_type
        
    def draw(self):
        # Save canvas state
        self.canv.saveState()
        
        if self.page_type == "header":
            # Draw header
            self.canv.setStrokeColor(colors.HexColor('#4F46E5'))  # Indigo
            self.canv.setFillColor(colors.HexColor('#4F46E5'))
            self.canv.rect(0, 0, self.width, self.height, fill=1)
            
            # Add text
            self.canv.setFillColor(colors.white)
            self.canv.setFont(BOLD_FONT, 14)
            self.canv.drawString(15, self.height-20, self.report_title)
            
            # Add date on the right
            date_str = datetime.now().strftime('%Y-%m-%d')
            self.canv.setFont(FONT_NAME, 10)
            self.canv.drawRightString(self.width-15, self.height-20, date_str)
        else:
            # Draw footer with page number
            page_num = self.canv.getPageNumber()
            self.canv.setFont(FONT_NAME, 9)
            self.canv.setFillColor(colors.HexColor('#4B5563'))  # Gray
            page_text = f"Page {page_num}"
            self.canv.drawRightString(self.width-15, 15, page_text)
            
            # Add company name or other info on left
            self.canv.drawString(15, 15, "Donor Analysis Report")
        
        # Restore canvas state
        self.canv.restoreState()

def format_metric_value(value):
    """Format metric values for display"""
    if isinstance(value, (int, float)):
        if abs(value) >= 1000000:
            return f"${value/1000000:.2f}M"
        elif abs(value) >= 1000:
            return f"${value/1000:.1f}K"
        else:
            return f"${value:.2f}"
    return str(value)

def create_donation_plots(donor_df, title="Donor Analysis"):
    """
    Create the 2x2 grid of donation plots using matplotlib with improved styling.
    
    Parameters:
    -----------
    donor_df : pandas DataFrame
        DataFrame containing donor information
    title : str
        Title for the plot
        
    Returns:
    --------
    str
        Path to the generated plot image
    """
    try:
        # Set custom style elements for plots
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['axes.edgecolor'] = '#CBD5E1'
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['figure.facecolor'] = '#F8FAFC'
        
        # Create a figure with 2x2 subplots
        plt.figure(figsize=(10, 8), dpi=150)
        # Add a slight background color
        plt.figure(figsize=(10, 8), dpi=150, facecolor='#F8FAFC')
        gs = GridSpec(2, 2, wspace=0.25, hspace=0.3)
        
        # Convert donation_date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(donor_df['donation_date']):
            donor_df['donation_date'] = pd.to_datetime(donor_df['donation_date'])
        
        # Create monthly aggregations
        donor_df['month'] = donor_df['donation_date'].dt.to_period('M')
        monthly_donations = donor_df.groupby('month').agg(
            sum=('donation_amount', 'sum'),
            count=('donation_amount', 'count')
        )
        monthly_donations.index = monthly_donations.index.to_timestamp()
        
        # Plot 1: Monthly donation amounts (top-left)
        ax1 = plt.subplot(gs[0, 0])
        ax1.plot(monthly_donations.index, monthly_donations['sum'], color='#3B82F6', linewidth=2.5)
        ax1.set_title('Monthly Donation Amounts', fontweight='bold', pad=10)
        ax1.set_ylabel('Amount ($)')
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Add shaded area under the line
        ax1.fill_between(monthly_donations.index, 0, monthly_donations['sum'], 
                        color='#3B82F6', alpha=0.2)
        
        # Format x-axis to show fewer dates
        if len(monthly_donations) > 6:
            ax1.xaxis.set_major_locator(plt.MaxNLocator(6))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Add subtle box around plot
        for spine in ax1.spines.values():
            spine.set_color('#CBD5E1')
        
        # Plot 2: Donation frequency (top-right)
        ax2 = plt.subplot(gs[0, 1])
        bars = ax2.bar(range(len(monthly_donations)), monthly_donations['count'], 
                     color='#10B981', alpha=0.8, width=0.8)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        ax2.set_title('Donation Frequency', fontweight='bold', pad=10)
        ax2.set_ylabel('Count')
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        # Set x-ticks to month names
        if len(monthly_donations) > 0:
            date_labels = [d.strftime('%b %Y') for d in monthly_donations.index]
            if len(date_labels) > 6:
                # Show fewer labels if there are many
                step = len(date_labels) // 6 + 1
                visible_labels = date_labels[::step]
                visible_positions = list(range(0, len(date_labels), step))
                ax2.set_xticks(visible_positions)
                ax2.set_xticklabels(visible_labels, rotation=45)
            else:
                ax2.set_xticks(range(len(date_labels)))
                ax2.set_xticklabels(date_labels, rotation=45)
        
        # Add subtle box around plot
        for spine in ax2.spines.values():
            spine.set_color('#CBD5E1')
        
        # Plot 3: Donation size distribution (bottom-left)
        ax3 = plt.subplot(gs[1, 0])
        n, bins, patches = ax3.hist(donor_df['donation_amount'], bins=15, 
                                  color='#F59E0B', alpha=0.8, edgecolor='white')
        
        # Change bin colors based on height
        cm = plt.cm.get_cmap('YlOrBr')
        bin_centers = 0.5 * (bins[:-1] + bins[1:])
        col = bin_centers - min(bin_centers)
        col /= max(col)
        
        for c, p in zip(col, patches):
            plt.setp(p, 'facecolor', cm(c))
            
        ax3.set_title('Donation Size Distribution', fontweight='bold', pad=10)
        ax3.set_xlabel('Donation Amount ($)')
        ax3.set_ylabel('Frequency')
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        # Add subtle box around plot
        for spine in ax3.spines.values():
            spine.set_color('#CBD5E1')
        
        # Plot 4: Cumulative donations (bottom-right)
        ax4 = plt.subplot(gs[1, 1])
        cumulative = donor_df.sort_values('donation_date')
        cumulative['cumulative'] = cumulative['donation_amount'].cumsum()
        
        # Add gradient line
        from matplotlib.collections import LineCollection
        from matplotlib.colors import LinearSegmentedColormap
        
        points = np.array([cumulative['donation_date'], cumulative['cumulative']]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # Create a colormap for the gradient
        cmap = LinearSegmentedColormap.from_list("", ["#FF0066", "#FF3366", "#FF6666", "#FF9966", "#FFCC66"])
        
        # Create a line collection
        lc = LineCollection(segments, cmap=cmap, linewidth=2.5)
        lc.set_array(np.linspace(0, 1, len(segments)))
        line = ax4.add_collection(lc)
        
        # Add shaded area under the line
        ax4.fill_between(cumulative['donation_date'], 0, cumulative['cumulative'], 
                        color='#FF6B6B', alpha=0.2)
        
        ax4.set_xlim(cumulative['donation_date'].min(), cumulative['donation_date'].max())
        ax4.set_ylim(0, cumulative['cumulative'].max() * 1.05)
        
        ax4.set_title('Cumulative Donations', fontweight='bold', pad=10)
        ax4.set_ylabel('Total Amount ($)')
        ax4.grid(True, linestyle='--', alpha=0.7)
        
        # Format x-axis to show fewer dates
        ax4.xaxis.set_major_locator(plt.MaxNLocator(6))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
        
        # Add subtle box around plot
        for spine in ax4.spines.values():
            spine.set_color('#CBD5E1')
        
        # Add a super title with nice styling
        plt.suptitle(title, fontsize=16, y=0.98, fontweight='bold')
        
        # Add a subtle background box behind the title
        fig = plt.gcf()
        fig.text(0.5, 0.96, '', ha='center', fontsize=16,
                bbox=dict(facecolor='#F0F9FF', edgecolor='#CBD5E1', boxstyle='round,pad=0.5'))
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            plt.savefig(tmp_path, bbox_inches='tight', dpi=150, facecolor='#F8FAFC')
            plt.close('all')
        
        return tmp_path
    
    except Exception as e:
        logger.error(f"Error creating donation plots: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create a simple error message image
        plt.figure(figsize=(10, 8), facecolor='#FFF5F5')
        plt.text(0.5, 0.5, f"Error: {str(e)}", 
                ha="center", va="center", fontsize=14, color='#DC2626',
                bbox=dict(facecolor='#FEE2E2', edgecolor='#EF4444', boxstyle='round,pad=1', alpha=0.8))
        
        # Save error image to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            plt.savefig(tmp_path, bbox_inches='tight', dpi=120)
            plt.close('all')
        
        return tmp_path

def generate_pdf_report(insights, filename,df=None):
    """Generate PDF report from insights and dataframe.
        
        Parameters:
        -----------
        insights : list
            List of insight dictionaries
        filename : str
            Original data filename
        df : pandas DataFrame, optional
            DataFrame containing the data, for generating column plots
        """ 
    try:
        logger.debug(f"Starting PDF generation for file: {filename}")
        logger.debug(f"Number of insights: {len(insights)}")
        
        # Create output directory if it doesn't exist
        output_dir = 'pdf_reports'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.debug(f"Created output directory: {output_dir}")
        
        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = os.path.join(output_dir, f"donor_analysis_{timestamp}.pdf")
        logger.debug(f"Output filename: {output_filename}")
        
        # Set up the PDF document with custom page layouts
        class PDFDocument(SimpleDocTemplate):
            def __init__(self, filename, **kw):
                SimpleDocTemplate.__init__(self, filename, **kw)
                self.report_title = "Donor Analysis Report"
                
            def handle_pageBegin(self):
                self.canv.saveState()
                # Skip header on the first page (title page)
                if self.canv.getPageNumber() > 1:
                    header = HeaderFooter(self.width + self.leftMargin + self.rightMargin, 
                                         0.75*inch, self.report_title, "header")
                    header.canv = self.canv
                    header.draw()
                # Add footer to all pages
                footer = HeaderFooter(self.width + self.leftMargin + self.rightMargin, 
                                     0.5*inch, self.report_title, "footer")
                footer.canv = self.canv
                footer.draw()
                self.canv.restoreState()
                SimpleDocTemplate.handle_pageBegin(self)
        
        # Create the document
        doc = PDFDocument(
            output_filename,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=70,  # Extra space for header
            bottomMargin=50  # Extra space for footer
        )
        logger.debug("Created PDF document template")
        
        # Initialize story and styles
        story = []
        styles = getSampleStyleSheet()
        
        # Create enhanced styles
        title_style = ParagraphStyle(
            'Title', 
            parent=styles['Heading1'],
            fontName=BOLD_FONT,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor('#4F46E5')  # Indigo
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=24,
            textColor=colors.HexColor('#6B7280')  # Gray
        )
        
        heading1_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontName=BOLD_FONT,
            fontSize=18,
            textColor=colors.HexColor('#4F46E5'),  # Indigo
            spaceAfter=10,
            leading=22
        )
        
        heading2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontName=BOLD_FONT,
            fontSize=16,
            textColor=colors.HexColor('#3B82F6'),  # Blue
            spaceAfter=8,
            spaceBefore=12,
            leading=20
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=11,
            spaceAfter=6,
            leading=14
        )
        
        # Create a highlighted message style
        highlight_style = ParagraphStyle(
            'Highlight',
            parent=normal_style,
            fontSize=12,
            textColor=colors.HexColor('#4F46E5'),  # Indigo
            backColor=colors.HexColor('#EEF2FF'),  # Light indigo
            borderColor=colors.HexColor('#C7D2FE'),  # Medium indigo
            borderWidth=1,
            borderPadding=5,
            borderRadius=5,
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        # Add title page with a clean design
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph('Donor Analysis Report', title_style))
        story.append(Spacer(1, 0.25*inch))
        story.append(Paragraph(f'Analysis of {filename}', subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Add a decorative line
        story.append(Table([['']], colWidths=[450], rowHeights=[1], 
                           style=[('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#4F46E5'))]))
        
        story.append(Spacer(1, 1*inch))
        
        # Add date and time with right alignment
        date_style = ParagraphStyle('Date', parent=normal_style, alignment=TA_RIGHT)
        story.append(Paragraph(f'Generated on: {datetime.now().strftime("%B %d, %Y at %H:%M")}', date_style))
        
        story.append(PageBreak())
        logger.debug("Added title page to PDF")
        
        # Track temporary files to clean up later
        temp_files = []
        
        # Create a table of contents
        toc_style = ParagraphStyle('TOC', parent=heading1_style)
        story.append(Paragraph('Table of Contents', toc_style))
        story.append(Spacer(1, 0.25*inch))
        
        # Add TOC entries
        toc_data = []
        for i, insight in enumerate(insights):
            insight_title = insight.get('type', '').replace('_', ' ').title()
            toc_data.append([f"{i+1}. {insight_title}", str(i+2)])  # Page numbers (title + TOC pages)
        
        toc_table = Table(toc_data, colWidths=[400, 50])
        toc_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), FONT_NAME),
            ('FONT', (1, 0), (1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4F46E5')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(toc_table)
        story.append(PageBreak())
        
        # Process each insight
        for i, insight in enumerate(insights):
            try:
                logger.debug(f"Processing insight {i+1}/{len(insights)}: {insight.get('type', 'unknown')}")
                
                # Add insight title with decorative styling
                insight_title = insight.get('type', '').replace('_', ' ').title()
                insight_num = f"{i+1}. "
                story.append(Paragraph(f"{insight_num}{insight_title}", heading1_style))
                
                # Add a decorative line
                story.append(Table([['']], colWidths=[450], rowHeights=[1], 
                                  style=[('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#3B82F6'))]))
                story.append(Spacer(1, 0.1*inch))
                
                # Add main message with highlight box
                if 'message' in insight:
                    # Create a highlighted message
                    message_text = insight['message'].replace('$', '\$')  # Escape $ for ReportLab
                    story.append(Paragraph(message_text, highlight_style))
                
                # Get details
                details = insight.get('details', {})
                
                # First add visualization if available
                if 'data' in details:
                    story.append(Paragraph('Data Visualization', heading2_style))
                    
                    try:
                        # If 'data' contains a DataFrame, use it to create plots
                        donor_data = details['data']
                        logger.debug(f"Found data DataFrame with {len(donor_data)} rows")
                        
                        # Generate plots using the data with entity name in title
                        entity_name = details.get('entity_name', '')
                        plot_title = f"{insight_title}: {entity_name}" if entity_name else insight_title
                        
                        # Create plots with enhanced styling
                        plot_path = create_donation_plots(donor_data, title=plot_title)
                        
                        # Create the image with full page width
                        available_width = doc.width
                        img_height = available_width * 0.8  # Maintain aspect ratio
                        
                        img = Image(plot_path, width=available_width, height=img_height)
                        story.append(img)
                        temp_files.append(plot_path)
                        logger.debug("Added data visualization to PDF")
                    except Exception as e:
                        logger.error(f"Error creating plot from data: {str(e)}")
                        logger.error(traceback.format_exc())
                        story.append(Paragraph(f"Plot could not be generated: {str(e)}", normal_style))
                    
                    story.append(Spacer(1, 0.2*inch))
                
                # Add metrics if available - show ALL metrics with better styling
                if 'metrics' in details:
                    metrics = details['metrics']
                    metrics_data = []
                    
                    # Only process and display non-empty metrics
                    for key, value in metrics.items():
                        if isinstance(value, (int, float, str)) and not isinstance(value, dict):
                            formatted_key = key.replace('_', ' ').title()
                            formatted_value = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
                            metrics_data.append([formatted_key, formatted_value])
                    
                    # Only show metrics section if there are metrics to display
                    if metrics_data:
                        story.append(Paragraph('Key Metrics', heading2_style))
                        
                        # SMALLER TABLE STYLING - reduced font size, padding and column widths
                        table_style = [
                            ('FONT', (0, 0), (-1, -1), FONT_NAME),
                            ('FONTSIZE', (0, 0), (-1, -1), 9),  # Reduced font size from 11 to 9
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('PADDING', (0, 0), (-1, -1), 6),  # Reduced padding from 12 to 6
                            ('TOPPADDING', (0, 0), (-1, -1), 6),  # Reduced from 12 to 6
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  # Reduced from 12 to 6
                            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#C7D2FE')),
                            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['#F9FAFB', '#F3F4F6']),
                            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                        ]
                        
                        # Add header row
                        metrics_data.insert(0, ["Metric", "Value"])
                        
                        # If we have lots of metrics, create a more compact multi-column table
                        if len(metrics_data) > 8:  # Including header
                            # Split into two columns
                            col1 = metrics_data[:1] + metrics_data[1:len(metrics_data)//2+1]
                            col2 = metrics_data[:1] + metrics_data[len(metrics_data)//2+1:]
                            
                            # Create tables for each column with smaller widths
                            metrics_table_1 = Table(col1, colWidths=[150, 80])  # Reduced from 200, 100
                            metrics_table_1.setStyle(TableStyle(table_style))
                            
                            metrics_table_2 = Table(col2, colWidths=[150, 80])  # Reduced from 200, 100
                            metrics_table_2.setStyle(TableStyle(table_style))
                            
                            # Create a container table with reduced spacing
                            container_data = [[metrics_table_1, metrics_table_2]]
                            container_table = Table(container_data, colWidths=[240, 240])  # Reduced from 310, 310
                            container_table.setStyle(TableStyle([
                                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ('RIGHTPADDING', (0, 0), (0, 0), 10),  # Reduced from 15 to 10
                                ('LEFTPADDING', (1, 0), (1, 0), 10),   # Reduced from 15 to 10
                            ]))
                            story.append(container_table)
                        else:
                            # Simple table with reduced widths
                            metrics_table = Table(metrics_data, colWidths=[220, 110])  # Reduced from 300, 150
                            metrics_table.setStyle(TableStyle(table_style))
                            story.append(metrics_table)
                        
                        story.append(Spacer(1, 0.2*inch))  # Reduced from 0.3 to 0.2 inch
                        logger.debug("Added metrics table to PDF")
                
                # Add recommendations with styled bullets
                if 'recommendations' in details:
                    story.append(Paragraph('Recommendations', heading2_style))
                    
                    # Create a table for recommendations with colored bullets
                    rec_data = []
                    for rec in details['recommendations']:
                        rec_data.append([
                            "•", 
                            Paragraph(rec, normal_style)
                        ])
                    
                    if rec_data:
                        rec_table = Table(rec_data, colWidths=[15, 435])
                        rec_table.setStyle(TableStyle([
                            ('FONT', (0, 0), (0, -1), BOLD_FONT),
                            ('FONTSIZE', (0, 0), (0, -1), 14),
                            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#3B82F6')),  # Blue bullets
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ]))
                        story.append(rec_table)
                    
                    story.append(Spacer(1, 0.2*inch))
                    logger.debug("Added recommendations to PDF")
                
                # Add a decorative footer for the section
                story.append(Table([['']], colWidths=[450], rowHeights=[1], 
                                  style=[('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB'))]))
                story.append(Spacer(1, 0.2*inch))
                
                # Add a page break after each insight
                if i < len(insights) - 1:
                    story.append(PageBreak())
                
            except Exception as e:
                logger.error(f"Error processing insight {insight.get('type', 'unknown')}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
       
        # Add column analysis section if dataframe is provided
        if df is not None and not df.empty:
            try:
                # Add section header
                story.append(PageBreak())
                story.append(Paragraph("Column Analysis", heading1_style))
                story.append(Spacer(1, 0.2*inch))
                
                # Intro text
                story.append(Paragraph(
                    "This section contains detailed visualizations for each column in the dataset, "
                    "showing distributions and patterns for individual variables.",
                    normal_style
                ))
                story.append(Spacer(1, 0.2*inch))
                
                # Create and add plots for each column
                for i, col_name in enumerate(df.columns):
                    # Generate plot for this column
                    plot_path = create_column_plot(df, col_name)
                    temp_files.append(plot_path)
                    
                    # Add column name as heading
                    story.append(Paragraph(f"{col_name}", heading2_style))
                    
                    # Add the plot image
                    img_width = 450  # Full width plot
                    story.append(Image(plot_path, width=img_width, height=img_width*0.6))
                    
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Add a decorative separator if not the last item
                    if i < len(df.columns) - 1:
                        story.append(Table([['']], colWidths=[450], rowHeights=[1], 
                                          style=[('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB'))]))
                        story.append(Spacer(1, 0.3*inch))
                
                logger.debug(f"Added {len(df.columns)} column plots to PDF")
                
            except Exception as e:
                logger.error(f"Error adding column plots: {str(e)}")
                logger.error(traceback.format_exc())
        else:
            logger.debug("No dataframe provided, skipping column analysis")
       
       
       
        # Build PDF
        logger.debug("Building PDF document")
        doc.build(story)
        logger.debug("PDF built successfully")
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                logger.error(f"Error removing temp file {temp_file}: {str(e)}")
        
        logger.debug(f"PDF generation complete: {output_filename}")
        return output_filename
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        logger.error(traceback.format_exc())
        raise



def create_column_plot(df, column):
    """
    Create a matplotlib plot for a single column.
    
    Parameters:
    -----------
    df : pandas DataFrame
        DataFrame containing the data
    column : str
        Column name to plot
        
    Returns:
    --------
    str
        Path to the generated plot image
    """
    try:
        # Set custom style elements for plots
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.linestyle'] = ':'
        plt.rcParams['grid.alpha'] = 0.7
        plt.rcParams['grid.color'] = '#CCCCCC'
        
        # Create a figure
        plt.figure(figsize=(10, 6), dpi=150)
        
        # Generate appropriate plot based on data type
        if pd.api.types.is_numeric_dtype(df[column]):
            # For numeric data, create a histogram (blue)
            plt.hist(df[column].dropna(), bins=15, color='blue', edgecolor='white', alpha=0.7)
            plt.xlabel(column)
            plt.ylabel('Frequency')
            plt.title(f'Distribution of {column}', fontweight='bold')
        else:
            # For categorical data, create a bar chart (green)
            value_counts = df[column].value_counts().sort_values(ascending=False)
            # Limit to top 15 categories if there are too many
            if len(value_counts) > 15:
                value_counts = value_counts.head(15)
                plt.title(f'Top 15 Values for {column}', fontweight='bold')
            else:
                plt.title(f'Distribution of {column}', fontweight='bold')
                
            plt.bar(range(len(value_counts)), value_counts.values, color='green')
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
            plt.xlabel(column)
            plt.ylabel('Count')
            
            # Add value labels on top of bars
            for i, v in enumerate(value_counts.values):
                plt.text(i, v + (max(value_counts.values) * 0.02), str(v), 
                        ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            plt.savefig(tmp_path, bbox_inches='tight')
            plt.close()
        
        return tmp_path
    
    except Exception as e:
        logger.error(f"Error creating plot for column {column}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Create a simple error message image
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"Error plotting {column}: {str(e)}", 
                ha="center", va="center", fontsize=14, color='red')
        
        # Save error image to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            plt.savefig(tmp_path, bbox_inches='tight')
            plt.close()
        
        return tmp_path