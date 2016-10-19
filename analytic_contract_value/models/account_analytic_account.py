# -*- coding: utf-8 -*-
# © 2015 Eficent - Jordi Ballester Alomar
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp


class AccountAnalyticAccount(orm.Model):
    _inherit = 'account.analytic.account'

    def list_lines_with_contract_value(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {}
        for curr_id in ids:
            res[curr_id] = {}
            # Now add the children
            cr.execute(
                """SELECT COALESCE(sum(amount),0.0) AS total_value
                FROM account_analytic_line_plan AS L
                LEFT JOIN account_analytic_account AS A
                ON L.account_id = A.id
                INNER JOIN account_account AC
                ON L.general_account_id = AC.id
                INNER JOIN account_account_type AT
                ON AT.id = AC.user_type
                WHERE AT.report_type = 'income'
                AND l.account_id = %s
                AND a.active_analytic_planning_version = l.version_id
                """, [curr_id])
            val = cr.fetchone() or 0
            res[curr_id] = val[0] if type(val) is tuple else val
        return res

    def list_accounts_with_contract_value(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = {}
        for curr_id in ids:
            # all_acc = []
            # res[curr_id] = {}
            # # Now add the children
            # cr.execute('''
            # WITH RECURSIVE children AS (
            # SELECT parent_id, id
            # FROM account_analytic_account
            # WHERE parent_id = %s
            # UNION ALL
            # SELECT a.parent_id, a.id
            # FROM account_analytic_account a
            # JOIN children b ON(a.parent_id = b.id)
            # )
            # SELECT * FROM children order by parent_id
            # ''', (curr_id,))
            # cr_res = cr.fetchall()
            # for x, y in cr_res:
            #     all_acc.append(y)
            # all_acc.append(curr_id)
            all_acc = [account for account in self.get_child_accounts(
                cr, uid, [curr_id], context)]

            contract_value = 0.0
            for account in self.browse(cr, uid, all_acc, context=context):
                if account.contract_value:
                    contract_value += account.contract_value
            res[curr_id] = contract_value
        return res

    def _total_contract_value_calc(self, cr, uid, ids, prop, unknow_none,
                                   unknow_dict):
        res = {}
        res = self.list_accounts_with_contract_value(cr, uid, ids,
                                                          context=None)
        # for acc_id in acc_list.keys():
        #     res[acc_id] = 0.0
        #     for ch_acc_id in acc_list[acc_id]:
        #         res[acc_id] += acc_list[acc_id][ch_acc_id]
        return res

    def _original_contract_value_calc(self, cr, uid, ids, prop, unknow_none,
                                   unknow_dict):
        return self.list_lines_with_contract_value(cr, uid, ids,
                                                          context=None)


    _columns = {
        'contract_value': fields.function(
            _original_contract_value_calc, method=True, type='float',
            string='Original Contract Value',
            help='Total contract value for this account'),
        'total_contract_value': fields.function(
            _total_contract_value_calc, method=True, type='float',
            string='Current Total Contract Value',
            help='Total Contract Value including child analytic accounts')
    }
