# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L. <contact@eficent.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, orm
from openerp.tools.translate import _


class AccountAnalyticLinePlan(orm.Model):
    _inherit = 'account.analytic.line.plan'

    _columns = {
        'change_id': fields.many2one('change.management.change',
                                     'Plan Change', required=False,
                                     ondelete='cascade'),
    }


class ChangeManagementChange(orm.Model):
    _inherit = 'change.management.change'

    _columns = {
        'change_value': fields.float('Value',
                                     readonly=True,
                                     help="Value of the Change",
                                     states={'draft': [('readonly', False)]}),
        'line_ids': fields.one2many('account.analytic.line.plan',
                                    'change_id', 'Lines'),
    }

    def set_state_draft(self, cr, uid, ids, *args):
        res = super(ChangeManagementChange, self).set_state_draft(
            cr, uid, ids)

        for change in self.browse(cr, uid, ids, context=None):
            for line in change.line_ids:
                line.unlink()
        return res

    def set_state_accepted(self, cr, uid, ids, *args):
        res = super(ChangeManagementChange, self).set_state_accepted(
            cr, uid, ids)
        analytic_obj = self.pool['account.analytic.account']
        for change in self.browse(cr, uid, ids, context=None):
            if not change.change_project_id:
                raise orm.except_orm(_("Error!"),
                                     _("A Change Management Project must be "
                                       "provided."))
            analytic_obj.write(
                cr, uid, [change.change_project_id.analytic_account_id.id],
                {'contract_value': change.change_value}, context=None)

            res = self.create_analytic_plan_lines(cr, uid, ids, context=None)

        return res

    def _prepare_analytic_line_plan_common(self, cr, uid, template_id, obj,
                                           context=None):

        return {
            'account_id': obj.change_project_id.analytic_account_id.id,
            'name': obj.project_id.name,
            'date': obj.date_registered,
            'currency_id': template_id.currency_id.id,
            'user_id': uid,
            'company_id': obj.change_project_id.company_id.id,
            'version_id': template_id.version_id.id
        }

    def _prepare_analytic_line_plan(self, cr, uid, template_id, product,
                                    amount_currency, type, common, obj,
                                    context=None):

        plan_line_obj = self.pool['account.analytic.line.plan']

        am = plan_line_obj.on_change_amount_currency(
            cr, uid, False, amount_currency,
            template_id.currency_id.id,
            obj.project_id.company_id.id, context=context)

        if am and 'value' in am and 'amount' in am['value']:
            amount = am['value']['amount']
        else:
            amount = item.labor_cost

        if type == 'expense':
            general_account_id = product.product_tmpl_id. \
                property_account_expense.id
            if not general_account_id:
                general_account_id = product.categ_id. \
                    property_account_expense_categ.id
        else:
            general_account_id = product.product_tmpl_id. \
                property_account_income.id
            if not general_account_id:
                general_account_id = product.categ_id. \
                    property_account_income_categ.id
        if not general_account_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no expense or income account '
                                   'defined for this product: "%s" (id:%d)')
                                 % (product.name,
                                    product.id,))
        if type == 'expense':
            journal_id = product.expense_analytic_plan_journal_id \
                         and product.expense_analytic_plan_journal_id.id \
                         or False
        else:
            journal_id = product.revenue_analytic_plan_journal_id \
                         and product.revenue_analytic_plan_journal_id.id \
                         or False
        if not journal_id:
            raise orm.except_orm(_('Error !'),
                                 _('There is no planning expense or revenue '
                                   'journals defined for this product: '
                                   '"%s" (id:%d)') % (product.name,
                                                      product.id,))
        if type == 'expense':
            amount_currency *= -1
            amount *= -1

        data = {
            'amount_currency': amount_currency,
            'amount': amount,
            'product_id': product.id,
            'product_uom_id': template_id.labor_cost_product_id.uom_id.id,
            'general_account_id': general_account_id,
            'journal_id': journal_id,
            'change_id': obj.id,
        }
        data.update(common)
        return data

    def create_analytic_plan_lines(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            change = obj
        plan_lines = self.pool.get('account.analytic.account').\
            list_accounts_with_contract_value(cr, uid, [change.change_project_id.id],
                                              context)
        analytic_line_plan_obj = self.pool['account.analytic.line.plan']
        template_id = change.project_id.company_id.template_id

        if not template_id:
            raise orm.except_orm(_("Error!"),
                                 _("No template is defined for this company"))

        for item in plan_lines:
            common = self._prepare_analytic_line_plan_common(
                cr, uid, template_id, change, context=context)
            # Create Revenue
            if change.change_value:
                plan_line_data_revenue = \
                    self._prepare_analytic_line_plan(
                        cr, uid, template_id, template_id.revenue_product_id,
                        change.change_value, 'revenue', common, change,
                        context=context)
                plan_line_id = analytic_line_plan_obj.create(
                    cr, uid, plan_line_data_revenue, context=context)
                res.append(plan_line_id)

        return {
            'domain': "[('id','in', [" + ','.join(map(str, res)) + "])]",
            'name': _('Analytic Plan Lines'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line.plan',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
    }