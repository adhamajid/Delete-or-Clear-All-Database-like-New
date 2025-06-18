# Delete records

def remove_data(env, model_names, seq_prefixes=[]):
    for model_name in model_names:
        try:
            if not env['ir.model']._get(model_name):
                continue
            table_name = env[model_name]._table
            env.cr.execute(f"DELETE FROM {table_name}")
            env.cr.commit()
        except Exception as e:
            raise UserError(f"Gagal menghapus data dari model {model_name}: {str(e)}")

    for prefix in seq_prefixes:
        domain = ['|', ('code', '=ilike', prefix + '%'), ('prefix', '=ilike', prefix + '%')]
        try:
            seqs = env['ir.sequence'].sudo().search(domain)
            if seqs:
                seqs.write({'number_next': 1})
        except Exception as e:
            raise UserError(f"Gagal reset sequence untuk prefix {prefix}: {str(e)}")

# ========== MAIN LOGIC UNTUK SERVER ACTION ==========

try:
    to_removes = [
        'payment.transaction',
        'account.bank.statement.line',
        'account.payment',
        'account.analytic.line',
        'account.analytic.account',
        'account.partial.reconcile',
        'account.move.line',
        'hr.expense.sheet',
        'account.move',
    ]

    remove_data(env, to_removes, [])

    domain = [
        ('company_id', '=', env.company.id),
        '|', ('code', '=ilike', 'account.%'),
        '|', ('prefix', '=ilike', 'BNK1/%'),
        '|', ('prefix', '=ilike', 'CSH1/%'),
        '|', ('prefix', '=ilike', 'INV/%'),
        '|', ('prefix', '=ilike', 'EXCH/%'),
        '|', ('prefix', '=ilike', 'MISC/%'),
        '|', ('prefix', '=ilike', '账单/%'),
        ('prefix', '=ilike', '杂项/%')
    ]

    try:
        seqs = env['ir.sequence'].search(domain)
        if seqs.exists():
            seqs.write({'number_next': 1})
    except Exception as e:
        raise UserError(f"Gagal reset sequence data: {str(e)}")

except Exception as final_error:
    raise UserError(f"Terjadi kesalahan saat menghapus data: {str(final_error)}")

# ========== MAIN LOGIC UNTUK SERVER ACTION ==========
to_removes = [
    'stock.quant',
    'stock.move.line',
    'stock.package_level',
    'stock.quantity.history',
    'stock.quant.package',
    'stock.move',
    'stock.picking',
    'stock.scrap',
    'stock.picking.batch',
    'stock.inventory.line',
    'stock.inventory',
    'stock.valuation.layer',
    'stock.lot',
    'procurement.group',
]
seqs = [
    'stock.',
    'picking.',
    'procurement.group',
    'product.tracking.default',
    'WH/',
]

try:
    remove_data(env, to_removes, seqs)
    # res = env['your.model'].remove_data(to_removes, seqs)
except Exception as e:
    raise UserError(f"Gagal menghapus data stock/lot: {str(e)}")

# ========== MAIN LOGIC ==========

try:
    company_id = env.company.id
    new_env = env(context=dict(env.context, force_company=company_id, company_id=company_id))

    to_removes = [
        # 'account.payment.method',
        # 'account.payment.method.line',
        'res.partner.bank',
        'account.move.line',
        'account.invoice',
        'account.payment',
        'account.bank.statement',
        'account.tax.account.tag',
        'account.tax',
        'account.account.account.tag',
        'wizard_multi_charts_accounts',
        'account.journal',
        'account.account',
    ]

    try:
        field1 = new_env['ir.model.fields']._get('product.template', "taxes_id").id
        field2 = new_env['ir.model.fields']._get('product.template', "supplier_taxes_id").id

        sql = f"DELETE FROM ir_default WHERE (field_id = {field1} OR field_id = {field2}) AND company_id = {company_id}"
        sql2 = f"UPDATE account_journal SET bank_account_id = NULL WHERE company_id = {company_id}"
        new_env.cr.execute(sql)
        new_env.cr.execute(sql2)
        new_env.cr.commit()
    except Exception as e:
        raise UserError(f"Gagal hapus default pajak dan akun jurnal: {str(e)}")

    if new_env['ir.model']._get('pos.config'):
        new_env['pos.config'].write({'journal_id': False})
    try:
        for pay in new_env['account.payment.method.line'].search([]):
            pay.write({'payment_account_id': None})
    except Exception as e:
        raise UserError(f"Gagal reset payment_account_id di payment method line: {str(e)}")
    try:
        for partner in new_env['res.partner'].search([]):
            partner.write({
                'property_account_receivable_id': None,
                'property_account_payable_id': None,
            })
    except Exception as e:
        raise UserError(f"Gagal reset akun partner: {str(e)}")

    try:
        for categ in new_env['product.category'].search([]):
            if categ.property_valuation != 'manual_periodic':
                categ.write({
                    'property_valuation': 'manual_periodic',
                })
            categ.write({
                'property_account_income_categ_id': None,
                'property_account_expense_categ_id': None,
                'property_account_creditor_price_difference_categ': None,
                'property_stock_account_input_categ_id': None,
                'property_stock_account_output_categ_id': None,
                'property_stock_valuation_account_id': None,
                # Tidak ubah property_valuation biar nggak error karena stock negatif
            })
    except Exception as e:
        raise UserError(f"Gagal reset akun kategori produk: {str(e)}")

    try:
        for tmpl in new_env['product.template'].search([]):
            tmpl.write({
                'property_account_income_id': None,
                'property_account_expense_id': None,
            })
    except Exception as e:
        raise UserError(f"Gagal reset akun produk: {str(e)}")

    try:
        for loc in new_env['stock.location'].search([]):
            loc.write({
                'valuation_in_account_id': None,
                'valuation_out_account_id': None,
            })
    except Exception as e:
        raise UserError(f"Gagal reset akun lokasi: {str(e)}")

    seqs = []
    remove_data(new_env, to_removes, seqs)

except Exception as final_error:
    raise UserError(f"Terjadi kesalahan umum: {str(final_error)}")


# ========== MAIN LOGIC UNTUK SERVER ACTION ==========
to_removes = [
    'mrp.workcenter.productivity',
    'mrp.workorder',
    'mrp.production.workcenter.line',
    'change.production.qty',
    'mrp.production',
    'mrp.production.product.line',
    'mrp.unbuild',
    'change.production.qty',
    'sale.forecast.indirect',
    'sale.forecast',
]
seqs = [
    'mrp.',
]
try:
    remove_data(env, to_removes, seqs)
    # res = env['your.model'].remove_data(to_removes, seqs)
except Exception as e:
    raise UserError(f"Gagal menghapus data purchase: {str(e)}")



# ========== MAIN LOGIC UNTUK SERVER ACTION ==========
to_removes = [
    'purchase.order.line',
    'purchase.order',
    'purchase.requisition.line',
    'purchase.requisition',
]
seqs = [
    'purchase.',
]

try:
    remove_data(env, to_removes, seqs)
    # res = env['your.model'].remove_data(to_removes, seqs)
except Exception as e:
    raise UserError(f"Gagal menghapus data purchase: {str(e)}")



# ========== MAIN LOGIC UNTUK SERVER ACTION ==========
to_removes = [
    'sale.order.line',
    'sale.order',
]
seqs = [
    'sale',
]
try:
    remove_data(env, to_removes, seqs)
    # res = env['your.model'].remove_data(to_removes, seqs)
except Exception as e:
    raise UserError(f"Gagal menghapus data purchase: {str(e)}")



# ========== MAIN LOGIC ==========

to_removes = [
    'mail.message',
    'mail.followers',
    'mail.activity',
]
seqs = []
try:
    remove_data(env,to_removes,seqs)
except Exception as e:
    raise UserError(f"Gagal menghapus umum : {str(e)}")


