### 📄 Arquivo: `dashboard_data.json`

Este arquivo simula o que o seu backend entregaria para o front-end. Note que usei os dados da sua planilha de teste (**Referência CL.5982**).

```json
{
  "production_order": {
    "op_id": "2024-001",
    "reference": "POLO PREMIUM CL.5982",
    "tp_total": 11.6742,
    "tl_calculated": 10,
    "pulse_duration": 30,
    "total_batches": 24,
    "completed_batches": 8,
    "efficiency_realtime": 82.5
  },
  "active_carts": [
    {
      "cart_id": 108,
      "batch_number": 9,
      "status": "in_progress",
      "started_at": "2024-05-22T14:05:00Z",
      "estimated_finish": "2024-05-22T14:35:00Z",
      "is_delayed": false
    },
    {
      "cart_id": 109,
      "batch_number": 10,
      "status": "waiting",
      "started_at": null,
      "estimated_finish": null,
      "is_delayed": false
    },
    {
      "cart_id": 110,
      "batch_number": 11,
      "status": "waiting",
      "started_at": null,
      "estimated_finish": null,
      "is_delayed": false
    },
    {
      "cart_id": 111,
      "batch_number": 12,
      "status": "waiting",
      "started_at": null,
      "estimated_finish": null,
      "is_delayed": false
    }
  ]
}

```
