const convict = require('convict')

const config = convict({
  company: {
    name: { default: 'PT Nusantara Cipta Mandiri' },
    currency: { default: 'IDR' },
    tax_id: { default: '02.145.889.7-014.000' },
  },
  approval: {
    threshold: { default: 5000000 },
    require_second_approver_above: { default: 50000000 },
  },
  export: {
    page_size: { default: 200 },
    include_void: { default: false },
  },
  retention: {
    days: { default: 2555 },
  },
})

module.exports = config
