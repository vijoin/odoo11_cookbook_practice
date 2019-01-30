# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'

    name = fields.Char('Title', required=True)
    short_name = fields.Char('Short Title',
                             required=True,
                             size=100,
                             translate=False)
    notes = fields.Text('Internatl Notes')
    state = fields.Selection(
        [('draft','Not Available'),
         ('available','Available'),
         ('lost','Lost')],
        'State')
    description = fields.Html(string='Description',
                              sanitize=True,
                              strip_style=True,
                              translate=False,)
    cover = fields.Binary('Book Cover')
    cost_price = fields.Float('Book Cost',
                              dp.get_precision('Book Price'))
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_update = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages',
                           default=0,
                           help='Total book page count',
                           groups='base.group_user',
                           states={'lost': [('readonly', True)]},
                           copy=True,
                           index=False,
                           readonly=False,
                           required=False,
                           company_dependent=False,
                           )
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14,4),
    )
    author_ids = fields.Many2many(
        'res.partner',
        string = 'Authors'
    )
    active = fields.Boolean('Active')

    def name_get(self):
        result = []
        for record in self:
            result.append(
                (record.id,
                 "%s (%s)" % (record.name, record.date_release)
            ))
        return result