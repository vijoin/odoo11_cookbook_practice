# -*- coding: utf-8 -*-

from odoo import fields, models


class LibraryBook(models.Model):
    _name = 'library.book'

    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2many(
        'res.partner',
        string = 'Authors'
    )
