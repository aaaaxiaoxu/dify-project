import os
from datetime import datetime
from functools import lru_cache
from io import BytesIO
from xml.sax.saxutils import escape


def _safe_text(value):
    return escape(str(value or '')).replace('\n', '<br/>')


def _normalize_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_report_images(value):
    if not isinstance(value, list):
        return []

    images = []
    seen_urls = set()
    for item in value:
        if isinstance(item, str):
            image_url = item.strip()
            image_meta = {}
        elif isinstance(item, dict):
            image_url = str(item.get('image_url') or item.get('url') or '').strip()
            image_meta = item
        else:
            continue

        if not image_url or image_url in seen_urls:
            continue
        if not image_url.startswith(('http://', 'https://')):
            continue

        images.append(
            {
                'image_url': image_url,
                'diary_title': str(image_meta.get('diary_title') or '').strip(),
                'diary_date': str(image_meta.get('diary_date') or '').strip(),
                'location': str(image_meta.get('location') or '').strip(),
            }
        )
        seen_urls.add(image_url)
    return images


def _report_image_caption(item):
    date_text = str(item.get('diary_date') or '').strip()
    location_text = str(item.get('location') or '').strip()
    title_text = str(item.get('diary_title') or '').strip()

    if date_text and location_text:
        return f'{date_text}  {location_text}'
    if date_text and title_text:
        return f'{date_text}  {title_text}'
    return location_text or title_text or '旅行图片'


def _download_gallery_pil_image(image_url, max_size=(1400, 1400)):
    if not image_url:
        return None

    try:
        import requests
        from PIL import Image, ImageOps
    except ImportError:
        return None

    try:
        response = requests.get(image_url, timeout=8)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            prepared = image.copy()
            prepared.thumbnail(max_size)
            return prepared
    except Exception:
        return None


def _pil_image_to_buffer(image):
    if image is None:
        return None

    buffer = BytesIO()
    has_alpha = 'A' in image.getbands()
    save_image = image.copy()
    image_format = 'PNG' if has_alpha else 'JPEG'
    if image_format == 'JPEG' and save_image.mode != 'RGB':
        save_image = save_image.convert('RGB')
    save_kwargs = {'format': image_format}
    if image_format == 'JPEG':
        save_kwargs['quality'] = 88
    save_image.save(buffer, **save_kwargs)
    buffer.seek(0)
    return buffer


def build_travel_report_pdf(payload, output_path):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Image as PlatypusImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        return _build_travel_report_pdf_with_pillow(payload, output_path)

    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

    page_width, page_height = A4
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )

    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=base['Title'],
        fontName='STSong-Light',
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.white,
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=11,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#E2E8F0'),
    )
    meta_style = ParagraphStyle(
        'MetaText',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=9,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#BFDBFE'),
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=base['Heading2'],
        fontName='STSong-Light',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        'BodyTextCN',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=10.5,
        leading=18,
        textColor=colors.HexColor('#334155'),
        alignment=TA_LEFT,
    )
    list_style = ParagraphStyle(
        'ListTextCN',
        parent=body_style,
        leftIndent=10,
        bulletIndent=0,
        spaceAfter=4,
    )
    stat_value_style = ParagraphStyle(
        'StatValue',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0F172A'),
    )
    stat_label_style = ParagraphStyle(
        'StatLabel',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569'),
    )
    quote_style = ParagraphStyle(
        'QuoteText',
        parent=body_style,
        fontName='STSong-Light',
        fontSize=12,
        leading=22,
        alignment=TA_LEFT,
        textColor=colors.white,
    )
    report_image_caption_style = ParagraphStyle(
        'ReportImageCaption',
        parent=base['BodyText'],
        fontName='STSong-Light',
        fontSize=8.5,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.HexColor('#64748B'),
    )

    period = payload.get('period') or {}
    report = payload.get('report') or {}
    summary_stats = payload.get('summary_stats') or {}
    report_images = _normalize_report_images(payload.get('report_images'))
    if not report_images and payload.get('cover_image'):
        report_images = _normalize_report_images([payload.get('cover_image')])
    source = payload.get('source') or 'local'
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M')

    source_label = 'AI 工作流生成' if source == 'dify' else '本地智能总结'
    period_text = f"{period.get('start_date', '--')} 至 {period.get('end_date', '--')}"

    story = []

    header_table = Table(
        [
            [Paragraph(_safe_text(report.get('report_title') or '智能旅行总结'), title_style)],
            [Paragraph(_safe_text(report.get('report_subtitle') or ''), subtitle_style)],
            [Paragraph(_safe_text(f'{period_text}  |  {source_label}  |  生成时间 {generated_at}'), meta_style)],
        ],
        colWidths=[doc.width],
    )
    header_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
                ('LEFTPADDING', (0, 0), (-1, -1), 18),
                ('RIGHTPADDING', (0, 0), (-1, -1), 18),
                ('TOPPADDING', (0, 0), (-1, -1), 18),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 14))

    if report_images:
        image_title = Paragraph(_safe_text('旅行图片'), section_title_style)
        story.append(image_title)

        image_cards = []
        image_col_width = doc.width / 2 - 10
        for item in report_images:
            pil_image = _download_gallery_pil_image(item.get('image_url'))
            if pil_image is None:
                continue
            image_buffer = _pil_image_to_buffer(pil_image)
            if image_buffer is None:
                continue

            image_width = float(image_col_width - 20)
            image_height = min(150, image_width * (pil_image.height / max(pil_image.width, 1)))
            image_flowable = PlatypusImage(image_buffer, width=image_width, height=image_height)
            caption_flowable = Paragraph(_safe_text(_report_image_caption(item)), report_image_caption_style)
            card = Table(
                [[image_flowable], [caption_flowable]],
                colWidths=[image_width],
            )
            card.setStyle(
                TableStyle(
                    [
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FBFF')),
                        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#D9E8FF')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]
                )
            )
            image_cards.append(card)

        if image_cards:
            image_rows = []
            for index in range(0, len(image_cards), 2):
                left_card = image_cards[index]
                right_card = image_cards[index + 1] if index + 1 < len(image_cards) else ''
                image_rows.append([left_card, right_card])

            image_table = Table(
                image_rows,
                colWidths=[image_col_width, image_col_width],
                hAlign='LEFT',
            )
            image_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            story.append(image_table)
            story.append(Spacer(1, 16))

    stat_cells = []
    stats_pairs = [
        (summary_stats.get('diary_count', 0), '篇日记'),
        (summary_stats.get('city_count', 0), '个地点'),
        (summary_stats.get('total_distance_km', 0), '公里'),
        (
            '--'
            if summary_stats.get('avg_emotion_score') in (None, '', 'None')
            else (
                f"+{float(summary_stats.get('avg_emotion_score')):.1f}"
                if float(summary_stats.get('avg_emotion_score')) > 0
                else f"{float(summary_stats.get('avg_emotion_score')):.1f}"
            ),
            '平均情绪',
        ),
    ]
    for value, label in stats_pairs:
        cell = Table(
            [
                [Paragraph(_safe_text(value), stat_value_style)],
                [Paragraph(_safe_text(label), stat_label_style)],
            ],
            colWidths=[doc.width / 2 - 12],
        )
        cell.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
                    ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#E2E8F0')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ]
            )
        )
        stat_cells.append(cell)

    stats_table = Table(
        [
            [stat_cells[0], stat_cells[1]],
            [stat_cells[2], stat_cells[3]],
        ],
        colWidths=[doc.width / 2 - 6, doc.width / 2 - 6],
        rowHeights=[None, None],
        hAlign='LEFT',
    )
    stats_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(stats_table)
    story.append(Spacer(1, 18))

    def add_section(title, content_blocks):
        story.append(Paragraph(_safe_text(title), section_title_style))
        for block in content_blocks:
            story.append(block)
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 10))

    add_section(
        '旅程概述',
        [Paragraph(_safe_text(report.get('summary') or ''), body_style)],
    )

    highlight_blocks = [
        Paragraph(f"{index + 1}. {_safe_text(item)}", list_style)
        for index, item in enumerate(_normalize_list(report.get('highlights')))
    ]
    if highlight_blocks:
        add_section('高光时刻', highlight_blocks)

    add_section(
        '情绪回顾',
        [Paragraph(_safe_text(report.get('emotion_review') or ''), body_style)],
    )

    preference_blocks = [
        Paragraph(f"• {_safe_text(item)}", list_style)
        for item in _normalize_list(report.get('travel_preferences'))
    ]
    if preference_blocks:
        add_section('旅行偏好', preference_blocks)

    suggestion_blocks = [
        Paragraph(f"• {_safe_text(item)}", list_style)
        for item in _normalize_list(report.get('next_trip_suggestions'))
    ]
    if suggestion_blocks:
        add_section('下次旅行建议', suggestion_blocks)

    memory_quote = str(report.get('memory_quote') or '').strip()
    if memory_quote:
        quote_table = Table(
            [[Paragraph(_safe_text(memory_quote), quote_style)]],
            colWidths=[doc.width],
        )
        quote_table.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 18),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 18),
                    ('TOPPADDING', (0, 0), (-1, -1), 16),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
                ]
            )
        )
        story.append(Spacer(1, 6))
        story.append(quote_table)

    def _draw_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor('#0F6BFF'))
        canvas.roundRect(doc.leftMargin, page_height - 10 * mm, doc.width, 3 * mm, 1.5 * mm, fill=1, stroke=0)
        canvas.setFont('STSong-Light', 8)
        canvas.setFillColor(colors.HexColor('#94A3B8'))
        canvas.drawRightString(page_width - doc.rightMargin, 10 * mm, f'第 {doc_obj.page} 页')
        canvas.restoreState()

    doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)


@lru_cache(maxsize=1)
def _resolve_cjk_font_path():
    candidates = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/Songti.ttc',
        '/System/Library/Fonts/Supplemental/Heiti SC.ttc',
        '/Library/Fonts/Arial Unicode.ttf',
        '/Library/Fonts/Arial Unicode MS.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise RuntimeError('未找到可用的中文字体，无法导出 PDF')


def _build_travel_report_pdf_with_pillow(payload, output_path):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise RuntimeError('未安装可用的 PDF 导出依赖') from exc

    font_path = _resolve_cjk_font_path()
    builder = _PillowTravelReportBuilder(payload, output_path, Image, ImageDraw, ImageFont, ImageOps, font_path)
    builder.build()


class _PillowTravelReportBuilder:
    PAGE_WIDTH = 1240
    PAGE_HEIGHT = 1754
    MARGIN_X = 76
    TOP_MARGIN = 76
    BOTTOM_MARGIN = 92
    CARD_GAP = 28
    CARD_RADIUS = 34
    CARD_PADDING_X = 34
    CARD_PADDING_Y = 28

    def __init__(self, payload, output_path, image_module, draw_module, font_module, image_ops_module, font_path):
        self.payload = payload or {}
        self.output_path = output_path
        self.Image = image_module
        self.ImageDraw = draw_module
        self.ImageFont = font_module
        self.ImageOps = image_ops_module
        self.font_path = font_path
        self.colors = {
            'page': '#F3F8FF',
            'card': '#FFFFFF',
            'card_alt': '#F8FBFF',
            'border': '#D9E8FF',
            'title': '#0F172A',
            'subtitle': '#475569',
            'body': '#334155',
            'muted': '#64748B',
            'blue': '#0F6BFF',
            'blue_soft': '#E8F1FF',
            'green': '#15803D',
            'green_soft': '#EAF8EE',
            'dark': '#0F172A',
            'dark_soft': '#1E293B',
            'white': '#FFFFFF',
        }
        self.fonts = {
            'hero_title': self.ImageFont.truetype(self.font_path, 58),
            'hero_subtitle': self.ImageFont.truetype(self.font_path, 28),
            'meta': self.ImageFont.truetype(self.font_path, 20),
            'section': self.ImageFont.truetype(self.font_path, 34),
            'body': self.ImageFont.truetype(self.font_path, 26),
            'body_small': self.ImageFont.truetype(self.font_path, 24),
            'stat_value': self.ImageFont.truetype(self.font_path, 48),
            'stat_label': self.ImageFont.truetype(self.font_path, 24),
            'quote': self.ImageFont.truetype(self.font_path, 30),
        }
        self.pages = []
        self.page = None
        self.draw = None
        self.cursor_y = self.TOP_MARGIN

    def build(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self._new_page()
        self._draw_header()
        report_images = _normalize_report_images(self.payload.get('report_images'))
        if not report_images and self.payload.get('cover_image'):
            report_images = _normalize_report_images([self.payload.get('cover_image')])
        if report_images:
            self._draw_report_images_section(report_images)
        self._draw_stats_grid()
        self._draw_text_section('旅程概述', self._paragraph_specs(self._report_value('summary')))
        highlights = _normalize_list(self._report_value('highlights'))
        if highlights:
            self._draw_text_section('高光时刻', self._bullet_specs(highlights, numbered=True))
        self._draw_text_section('情绪回顾', self._paragraph_specs(self._report_value('emotion_review')))
        preferences = _normalize_list(self._report_value('travel_preferences'))
        if preferences:
            self._draw_text_section('旅行偏好', self._bullet_specs(preferences))
        suggestions = _normalize_list(self._report_value('next_trip_suggestions'))
        if suggestions:
            self._draw_text_section('下次旅行建议', self._bullet_specs(suggestions))
        quote_text = str(self._report_value('memory_quote') or '').strip()
        if quote_text:
            self._draw_quote_card(quote_text)
        self._draw_page_footers()
        images = [page.convert('RGB') for page in self.pages]
        images[0].save(
            self.output_path,
            'PDF',
            resolution=150.0,
            save_all=True,
            append_images=images[1:],
        )

    def _report_value(self, key):
        report = self.payload.get('report') or {}
        return report.get(key)

    def _summary_stats(self):
        return self.payload.get('summary_stats') or {}

    def _period_text(self):
        period = self.payload.get('period') or {}
        return f"{period.get('start_date', '--')} 至 {period.get('end_date', '--')}"

    def _source_text(self):
        return 'AI 工作流生成' if (self.payload.get('source') or 'local') == 'dify' else '本地智能总结'

    def _new_page(self):
        self.page = self.Image.new('RGB', (self.PAGE_WIDTH, self.PAGE_HEIGHT), self.colors['page'])
        self.draw = self.ImageDraw.Draw(self.page)
        self.pages.append(self.page)
        self.cursor_y = self.TOP_MARGIN
        self.draw.rounded_rectangle(
            (self.MARGIN_X, 28, self.PAGE_WIDTH - self.MARGIN_X, 42),
            radius=8,
            fill=self.colors['blue'],
        )

    def _draw_page_footers(self):
        footer_font = self.fonts['meta']
        for index, page in enumerate(self.pages, start=1):
            draw = self.ImageDraw.Draw(page)
            footer = f'第 {index} 页'
            text_width = self._text_width(footer, footer_font, draw)
            draw.text(
                (self.PAGE_WIDTH - self.MARGIN_X - text_width, self.PAGE_HEIGHT - 52),
                footer,
                font=footer_font,
                fill=self.colors['muted'],
            )

    def _draw_header(self):
        title = str(self._report_value('report_title') or '智能旅行总结').strip()
        subtitle = str(self._report_value('report_subtitle') or '').strip()
        meta = f"{self._period_text()}  |  {self._source_text()}  |  生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        card_x = self.MARGIN_X
        card_y = self.cursor_y
        card_w = self.PAGE_WIDTH - self.MARGIN_X * 2
        title_lines = self._wrap_text(title, self.fonts['hero_title'], card_w - 140)
        subtitle_lines = self._wrap_text(subtitle, self.fonts['hero_subtitle'], card_w - 140) if subtitle else []
        meta_lines = self._wrap_text(meta, self.fonts['meta'], card_w - 140)

        line_gap = 12
        body_height = (
            len(title_lines) * self._line_height(self.fonts['hero_title'], line_gap)
            + len(subtitle_lines) * self._line_height(self.fonts['hero_subtitle'], 8)
            + len(meta_lines) * self._line_height(self.fonts['meta'], 0)
        )
        card_h = max(290, body_height + 120)

        self._rounded_card(card_x, card_y, card_w, card_h, self.colors['dark'])
        top_y = card_y + 40
        self._draw_center_lines(title_lines, self.fonts['hero_title'], self.colors['white'], top_y, line_gap)
        top_y += len(title_lines) * self._line_height(self.fonts['hero_title'], line_gap) + 10
        if subtitle_lines:
            self._draw_center_lines(subtitle_lines, self.fonts['hero_subtitle'], '#D7E7FF', top_y, 8)
            top_y += len(subtitle_lines) * self._line_height(self.fonts['hero_subtitle'], 8) + 14
        self._draw_center_lines(meta_lines, self.fonts['meta'], '#BFD7FF', top_y, 0)
        self.cursor_y = card_y + card_h + self.CARD_GAP

    def _draw_stats_grid(self):
        stats = self._summary_stats()
        values = [
            (str(stats.get('diary_count', 0)), '篇日记'),
            (str(stats.get('city_count', 0)), '个地点'),
            (self._format_distance(stats.get('total_distance_km', 0)), '公里'),
            (self._format_score(stats.get('avg_emotion_score')), '平均情绪'),
        ]
        total_w = self.PAGE_WIDTH - self.MARGIN_X * 2
        gap = 22
        card_w = (total_w - gap) / 2
        card_h = 190
        section_h = card_h * 2 + gap
        self._ensure_space(section_h)
        start_x = self.MARGIN_X
        start_y = self.cursor_y

        for index, (value, label) in enumerate(values):
            row = index // 2
            col = index % 2
            x = int(start_x + col * (card_w + gap))
            y = int(start_y + row * (card_h + gap))
            self._rounded_card(x, y, int(card_w), card_h, self.colors['card'])
            self.draw.rounded_rectangle(
                (x, y, x + int(card_w), y + card_h),
                radius=self.CARD_RADIUS,
                outline=self.colors['border'],
                width=2,
            )
            value_font = self.fonts['stat_value']
            label_font = self.fonts['stat_label']
            value_width = self._text_width(value, value_font)
            label_width = self._text_width(label, label_font)
            self.draw.text(
                (x + int((card_w - value_width) / 2), y + 54),
                value,
                font=value_font,
                fill=self.colors['blue'],
            )
            self.draw.text(
                (x + int((card_w - label_width) / 2), y + 122),
                label,
                font=label_font,
                fill=self.colors['muted'],
            )

        self.cursor_y = start_y + section_h + self.CARD_GAP

    def _draw_text_section(self, title, line_specs):
        if not line_specs:
            return

        title_font = self.fonts['section']
        body_area_width = self.PAGE_WIDTH - self.MARGIN_X * 2 - self.CARD_PADDING_X * 2
        line_index = 0
        continued = False

        while line_index < len(line_specs):
            title_text = f'{title}（续）' if continued else title
            title_h = self._line_height(title_font, 0)
            available_height = self.PAGE_HEIGHT - self.BOTTOM_MARGIN - self.cursor_y
            min_card_height = self.CARD_PADDING_Y * 2 + title_h + self._line_height(self.fonts['body'], 8) + 24

            if available_height < min_card_height:
                self._new_page()
                available_height = self.PAGE_HEIGHT - self.BOTTOM_MARGIN - self.cursor_y

            content_limit = available_height - self.CARD_PADDING_Y * 2 - title_h - 24
            used_height = 0
            chunk = []
            while line_index < len(line_specs):
                spec = line_specs[line_index]
                font = self.fonts[spec.get('font', 'body')]
                line_height = spec.get('height') or self._line_height(font, 8)
                if chunk and used_height + line_height > content_limit:
                    break
                chunk.append(spec)
                used_height += line_height
                line_index += 1

            if not chunk:
                self._new_page()
                continue

            card_h = int(self.CARD_PADDING_Y * 2 + title_h + used_height + 24)
            self._rounded_card(self.MARGIN_X, self.cursor_y, self.PAGE_WIDTH - self.MARGIN_X * 2, card_h, self.colors['card'])
            self.draw.rounded_rectangle(
                (
                    self.MARGIN_X,
                    self.cursor_y,
                    self.PAGE_WIDTH - self.MARGIN_X,
                    self.cursor_y + card_h,
                ),
                radius=self.CARD_RADIUS,
                outline=self.colors['border'],
                width=2,
            )
            title_x = self.MARGIN_X + self.CARD_PADDING_X
            title_y = self.cursor_y + self.CARD_PADDING_Y
            self.draw.text((title_x, title_y), title_text, font=title_font, fill=self.colors['title'])
            self.draw.rounded_rectangle(
                (title_x, title_y + title_h + 10, title_x + 96, title_y + title_h + 18),
                radius=4,
                fill=self.colors['blue'],
            )

            current_y = title_y + title_h + 34
            for spec in chunk:
                line_text = spec.get('text', '')
                line_height = spec.get('height')
                if line_height is None:
                    line_height = self._line_height(self.fonts[spec.get('font', 'body')], 8)
                if not line_text:
                    current_y += line_height
                    continue
                indent = spec.get('indent', 0)
                self.draw.text(
                    (title_x + indent, current_y),
                    line_text,
                    font=self.fonts[spec.get('font', 'body')],
                    fill=spec.get('fill', self.colors['body']),
                )
                current_y += line_height

            self.cursor_y += card_h + self.CARD_GAP
            continued = line_index < len(line_specs)

    def _draw_report_images_section(self, report_images):
        prepared = []
        for item in report_images:
            pil_image = _download_gallery_pil_image(item.get('image_url'))
            if pil_image is None:
                continue
            prepared.append(
                {
                    'image': pil_image,
                    'caption': _report_image_caption(item),
                }
            )

        if not prepared:
            return

        title_font = self.fonts['section']
        caption_font = self.fonts['body_small']
        title_height = self._line_height(title_font, 0)
        content_width = self.PAGE_WIDTH - self.MARGIN_X * 2 - self.CARD_PADDING_X * 2
        column_gap = 20
        tile_width = int((content_width - column_gap) / 2)
        image_height = 240
        caption_height = self._line_height(caption_font, 6) * 2
        tile_height = image_height + caption_height + 56
        row_gap = 16

        cursor = 0
        continued = False
        while cursor < len(prepared):
            title_text = '旅行图片（续）' if continued else '旅行图片'
            available_height = self.PAGE_HEIGHT - self.BOTTOM_MARGIN - self.cursor_y
            min_card_height = self.CARD_PADDING_Y * 2 + title_height + tile_height + 24
            if available_height < min_card_height:
                self._new_page()
                available_height = self.PAGE_HEIGHT - self.BOTTOM_MARGIN - self.cursor_y

            row_height = tile_height + row_gap
            content_limit = available_height - self.CARD_PADDING_Y * 2 - title_height - 24
            rows_fit = max(1, int((content_limit + row_gap) // row_height))
            take_count = min(len(prepared) - cursor, rows_fit * 2)
            rows_count = (take_count + 1) // 2
            card_height = int(self.CARD_PADDING_Y * 2 + title_height + 24 + rows_count * tile_height + max(0, rows_count - 1) * row_gap)

            card_x = self.MARGIN_X
            card_y = self.cursor_y
            card_w = self.PAGE_WIDTH - self.MARGIN_X * 2
            self._rounded_card(card_x, card_y, card_w, card_height, self.colors['card'])
            self.draw.rounded_rectangle(
                (card_x, card_y, card_x + card_w, card_y + card_height),
                radius=self.CARD_RADIUS,
                outline=self.colors['border'],
                width=2,
            )

            title_x = card_x + self.CARD_PADDING_X
            title_y = card_y + self.CARD_PADDING_Y
            self.draw.text((title_x, title_y), title_text, font=title_font, fill=self.colors['title'])
            self.draw.rounded_rectangle(
                (title_x, title_y + title_height + 10, title_x + 96, title_y + title_height + 18),
                radius=4,
                fill=self.colors['blue'],
            )

            row_y = title_y + title_height + 34
            for row_index in range(rows_count):
                for column_index in range(2):
                    item_index = cursor + row_index * 2 + column_index
                    if item_index >= cursor + take_count:
                        continue

                    tile_x = title_x + column_index * (tile_width + column_gap)
                    tile_y = row_y + row_index * (tile_height + row_gap)
                    self.draw.rounded_rectangle(
                        (tile_x, tile_y, tile_x + tile_width, tile_y + tile_height),
                        radius=24,
                        fill=self.colors['card_alt'],
                        outline=self.colors['border'],
                        width=2,
                    )
                    self._paste_gallery_image(prepared[item_index]['image'], tile_x + 12, tile_y + 12, tile_width - 24, image_height)

                    caption_lines = self._wrap_text(
                        prepared[item_index]['caption'],
                        caption_font,
                        tile_width - 24,
                        draw=self.draw,
                    )[:2]
                    caption_y = tile_y + 12 + image_height + 14
                    for line in caption_lines:
                        self.draw.text(
                            (tile_x + 12, caption_y),
                            line,
                            font=caption_font,
                            fill=self.colors['muted'],
                        )
                        caption_y += self._line_height(caption_font, 6)

            cursor += take_count
            self.cursor_y += card_height + self.CARD_GAP
            continued = cursor < len(prepared)

    def _draw_quote_card(self, quote_text):
        font = self.fonts['quote']
        line_specs = [{'text': line, 'font': 'quote', 'fill': self.colors['white']} for line in self._wrap_text(quote_text, font, self.PAGE_WIDTH - self.MARGIN_X * 2 - self.CARD_PADDING_X * 2 - 20)]
        total_height = self.CARD_PADDING_Y * 2 + len(line_specs) * self._line_height(font, 10) + 50
        self._ensure_space(total_height)

        x = self.MARGIN_X
        y = self.cursor_y
        w = self.PAGE_WIDTH - self.MARGIN_X * 2
        h = int(total_height)
        self._rounded_card(x, y, w, h, self.colors['dark_soft'])
        self.draw.text((x + 22, y + 8), '“', font=self.fonts['hero_title'], fill='#6EA8FF')

        current_y = y + self.CARD_PADDING_Y + 26
        for spec in line_specs:
            self.draw.text(
                (x + self.CARD_PADDING_X + 26, current_y),
                spec['text'],
                font=self.fonts['quote'],
                fill=spec['fill'],
            )
            current_y += self._line_height(self.fonts['quote'], 10)

        self.cursor_y += h + self.CARD_GAP

    def _paragraph_specs(self, text):
        content = str(text or '').strip()
        if not content:
            return []
        specs = []
        paragraphs = [part.strip() for part in content.split('\n') if part.strip()]
        max_width = self.PAGE_WIDTH - self.MARGIN_X * 2 - self.CARD_PADDING_X * 2
        for index, paragraph in enumerate(paragraphs):
            for line in self._wrap_text(paragraph, self.fonts['body'], max_width):
                specs.append({'text': line, 'font': 'body', 'fill': self.colors['body']})
            if index != len(paragraphs) - 1:
                specs.append({'text': '', 'height': 12})
        return specs

    def _bullet_specs(self, items, numbered=False):
        specs = []
        max_width = self.PAGE_WIDTH - self.MARGIN_X * 2 - self.CARD_PADDING_X * 2
        font = self.fonts['body']
        for index, item in enumerate(items, start=1):
            text = str(item or '').strip()
            if not text:
                continue
            prefix = f'{index}. ' if numbered else '• '
            continuation_indent = 34
            lines = self._wrap_text_with_prefix(text, font, max_width, prefix, continuation_indent)
            for line_index, line in enumerate(lines):
                specs.append(
                    {
                        'text': line['text'],
                        'font': 'body',
                        'fill': self.colors['body'],
                        'indent': line['indent'],
                    }
                )
            specs.append({'text': '', 'height': 8})
        if specs and not specs[-1].get('text'):
            specs.pop()
        return specs

    def _wrap_text_with_prefix(self, text, font, max_width, prefix, continuation_indent):
        prefix_width = self._text_width(prefix, font)
        first_width = max(80, int(max_width - prefix_width))
        other_width = max(80, int(max_width - continuation_indent))
        segments = self._wrap_text(text, font, first_width, draw=self.draw)
        if not segments:
            return [{'text': prefix, 'indent': 0}]

        lines = [{'text': prefix + segments[0], 'indent': 0}]
        for segment in segments[1:]:
            wrapped = self._wrap_text(segment, font, other_width, draw=self.draw)
            for item in wrapped:
                lines.append({'text': item, 'indent': continuation_indent})
        return lines

    def _wrap_text(self, text, font, max_width, draw=None):
        draw = draw or self.draw
        content = str(text or '').strip()
        if not content:
            return []

        lines = []
        for paragraph in content.split('\n'):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            current = ''
            for char in paragraph:
                trial = current + char
                if self._text_width(trial, font, draw) <= max_width or not current:
                    current = trial
                else:
                    lines.append(current)
                    current = char
            if current:
                lines.append(current)
        return lines

    def _line_height(self, font, extra_spacing=0):
        bbox = self.draw.textbbox((0, 0), '旅Ag', font=font)
        return (bbox[3] - bbox[1]) + extra_spacing

    def _text_width(self, text, font, draw=None):
        draw = draw or self.draw
        if not text:
            return 0
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]

    def _draw_center_lines(self, lines, font, fill, start_y, extra_spacing):
        if not lines:
            return
        line_height = self._line_height(font, extra_spacing)
        current_y = start_y
        for line in lines:
            width = self._text_width(line, font)
            x = int((self.PAGE_WIDTH - width) / 2)
            self.draw.text((x, current_y), line, font=font, fill=fill)
            current_y += line_height

    def _rounded_card(self, x, y, w, h, fill):
        self.draw.rounded_rectangle((x, y, x + w, y + h), radius=self.CARD_RADIUS, fill=fill)

    def _ensure_space(self, needed_height):
        if self.cursor_y + needed_height > self.PAGE_HEIGHT - self.BOTTOM_MARGIN:
            self._new_page()

    def _paste_gallery_image(self, image, x, y, width, height):
        prepared = image.copy()
        prepared = self.ImageOps.contain(prepared, (width, height))
        paste_x = x + int((width - prepared.width) / 2)
        paste_y = y + int((height - prepared.height) / 2)
        if prepared.mode == 'RGBA':
            self.page.paste(prepared, (paste_x, paste_y), prepared.split()[-1])
        else:
            self.page.paste(prepared, (paste_x, paste_y))

    @staticmethod
    def _format_distance(value):
        try:
            return f'{float(value):.1f}'
        except (TypeError, ValueError):
            return '--'

    @staticmethod
    def _format_score(value):
        try:
            score = float(value)
        except (TypeError, ValueError):
            return '--'
        return f'+{score:.1f}' if score > 0 else f'{score:.1f}'
