# -*- coding: utf-8 -*-

import os
from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.fields import Date as fDate
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class BaseArchive(models.AbstractModel):
    _name = 'base.archive'

    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active


class LibraryBook(models.Model):
    _name = 'library.book'
    _inherit = ['base.archive']
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'

    name = fields.Char('Title', required=True)
    short_name = fields.Char('Short Title',
                             #required=True,
                             size=100,
                             translate=False)
    category_id = fields.Many2one('library.book.category', 'Category')
    notes = fields.Text('Internatl Notes')
    state = fields.Selection(
        [('draft','Not Available'),
         ('available','Available'),
         ('borrowed', 'Borrowed'),
         ('lost','Lost')],
        'State')
    description = fields.Html(string='Description',
                              sanitize=True,
                              strip_style=True,
                              translate=False,)
    data = fields.Text()
    filename = fields.Char()
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
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price')
    publisher_id = fields.Many2one('res.partner', string='Publisher',
                                   ondelete='set null',
                                   context={},
                                   domain=[],
                                   )
    publisher_city = fields.Char(
        'Publisher City',
        related='publisher_id.city',
        readonly=True)
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,
        compute_sudo=False,
    )
    ref_docs_id = fields.Reference(
        selection='_referencable_models',
        string='Reference Document',
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

    _sql_constraints = [
        ('name_uniq',
         'UNIQUE (name)',
         'Book Title must be unique.')
    ]

    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if (record.date_release and
                    record.date_release > fields.Date.today()):
                raise models.ValidationError(
                    'Release date must be in the past.')

    @api.depends('date_release')
    def _compute_age(self):
        today = fDate.context_today(self)
        for book in self.filtered('date_release'):
            delta = today - book.date_release
            book.age_days = delta.days

    def _inverse_age(self):
        today = fDate.context_today(self)
        for book in self.filtered('date_release'):
            d = fDate.subtract(today, days=book.age_days)
            book.date_release = d

    def _search_age(self, operator, value):
        today = fDate.context_today(self)
        value_date = fDate.subtract(today, days=value)
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<',
            '>=': '<=',
            '<': '>',
            '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]

    @api.model
    def _referencable_models(self):

        #models = self.env['res.request.link'].search[()]
        #return [(x.object, x.name) for x in models]

        ref_list = [
            ('res.users','Users'),
            ('res.partner','Partners'),
        ]
        return ref_list

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available'),]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                continue

    @api.multi
    def try_change_state(self):
        self.change_state('lost')

    @api.multi
    def save_data(self):
        self.save(self.filename)

    @api.multi
    def save(self, filename):
        if '/' in filename or '\\' in filename:
            raise UserError('Illegal filename %s' % filename)
        path = os.path.join('/opt/exports', filename)
        try:
            with open(path, 'w') as fobj:
                for record in self:
                    fobj.write(record.data)
                    fobj.write('\n')
        except (IOError, OSError) as exc:
            message = _('Unable to save file: %s') % exc
            raise UserError(message)

    @api.model
    def get_all_library_members(self):
        library_member_model = self.env['library.member'].sudo()
        library_member_model.create({'name': 'Victor Inojosa'})
        return library_member_model.search([])

    @api.multi
    def log_members(self):
        _logger.info("\nMembers: %s\n" % self.get_all_library_members().mapped('name'))

    @api.multi
    def create_partner(self):
        record = self.env['res.partner'].create_partner()
        _logger.info("New Partners IDs: Parent %s and Children %s" % (record, record.child_ids))
        return record

    @api.model
    def add_contacts(self, partner, contacts):
        partner.ensure_one()
        if contacts:
            partner.date = fields.Date.context_today(self)
            partner.child_ids |= contacts

    @api.multi
    def button_add_contacts(self):
        for partner in self.author_ids:
            created_partner_id = self.create_partner()
            contact_ids = created_partner_id | created_partner_id.child_ids
            self.add_contacts(partner, contact_ids)

    @api.model
    def find_partners_and_contacts(self, name):
        partner = self.env['res.partner']

        domain = ['|',
                  '&',
                  ('is_company', '=', True),
                  ('name', 'ilike', name),
                  ('&'),
                  ('is_company', '=', False),
                  ('parent_id.name', 'ilike', name)
                  ]

        return partner.search(domain)

    def button_find_partners_contacts(self):
        partner_ids = self.find_partners_and_contacts("test")
        _logger.info("Found Partners IDs: %s Name: %s " % (partner_ids, partner_ids.mapped('name')))

    def button_test_combining_recordsets(self):
        partner_test_ids = self.find_partners_and_contacts("test")
        partner_prueba_ids = self.find_partners_and_contacts("prueba")

        recordset_1_ids = partner_test_ids + partner_prueba_ids
        _logger.info("recordset1 IDs: %s Name: %s " % (
        recordset_1_ids, recordset_1_ids.mapped('name')))

        recordset_1_ids = partner_test_ids + partner_prueba_ids
        _logger.info("recordset1 IDs: %s Name: %s " % (
            recordset_1_ids, recordset_1_ids.mapped('name')))

        recordset_2_ids = partner_test_ids | partner_prueba_ids
        _logger.info("recordset2 IDs: %s Name: %s " % (
            recordset_2_ids, recordset_2_ids.mapped('name')))

        recordset_3_ids = partner_test_ids & partner_prueba_ids
        _logger.info("recordset3 IDs: %s Name: %s " % (
            recordset_3_ids, recordset_3_ids.mapped('name')))

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    published_book_ids = fields.One2many(
        'library.book', 'publisher_id',
        string='Published Books')

    authored_book_ids = fields.Many2many('library.book', string='Authored Books',
                                         relation='library_book_res_partner_rel')
    count_books = fields.Integer(
        'Number of Authored Books',
        compute='_compute_count_books'
    )

    api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)

    @api.multi
    def create_partner(self):
        today_str = fields.Date.context_today(self)

        val1 = {'name': 'Eric Idle',
                'email': 'eric.idle@example.com',
                'date': today_str}

        val2 = {'name': 'John Clesse',
                'email': 'john.cleese@example.com',
                'date': today_str}

        partner_val = {
            'name': 'Flying Circus',
            'email': 'm.python@example.com',
            'date': today_str,
            'is_company': True,
            'child_ids': [
                            (0, 0, val1),
                            (0, 0, val2),
                         ]
                      }

        record = self.env['res.partner'].create(partner_val)
        return record

class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner',
                                 ondelete='cascade')
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of Birth')
