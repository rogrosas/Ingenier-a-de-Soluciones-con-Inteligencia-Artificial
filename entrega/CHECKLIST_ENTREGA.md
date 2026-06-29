# Checklist de Entrega — EP3 + EFT

**Agente "Banco Digital Chile" · ISY0101 · Roger Rosas · Rodrigo Santis · Edgardo Gutiérrez**

Marca cada ítem antes de entregar. Lo que está ✅ ya quedó hecho en el repositorio;
lo que está ⬜ depende del equipo.

---

## ✅ Ya listo (en el repositorio)

- [x] Código de observabilidad, trazabilidad y métricas (`observability/`)
- [x] Capa de seguridad y uso responsable (`security/`)
- [x] Pipeline RAG con fuentes internas + externas (`rag/`)
- [x] 22 pruebas automatizadas pasando (`tests/`, evidencia en `reports/evidencia_pruebas.txt`)
- [x] Dashboard: dataset Power BI + workbook Excel + guía DAX (`dashboard/`)
- [x] Informe EP3 (≤5 págs) — `entrega/EP3_Observabilidad_BancoDigitalChile.docx`
- [x] Informe EFT — `entrega/EFT_Informe_Final_BancoDigitalChile.docx`
- [x] Informe Integral consolidado — `entrega/Informe_Completo_BancoDigitalChile.docx`
- [x] Presentación de defensa — `entrega/EFT_Presentacion_Defensa.pptx`
- [x] Guion de la presentación — `entrega/GUION_PRESENTACION_EFT.docx`
- [x] Notebook ejecutable (Colab) — `entrega/EFT_Notebook_BancoDigitalChile.ipynb`
- [x] README de ejecución para el evaluador — `README_EP3.md`
- [x] Evidencia de ejecución — `entrega/evidencia/`

---

## ⬜ Pendiente del equipo (NO usar IA donde lo indica la pauta)

### Redacción propia (la pauta prohíbe IA en estas secciones)
- [ ] **Justificación técnica de diseño** (IE4) — sección 2.4 de los informes
- [ ] **Conclusiones del equipo** — sección final de los informes
- [ ] **Reflexión individual de Roger Rosas**
- [ ] **Reflexión individual de Rodrigo Santis**
- [ ] **Reflexión individual de Edgardo Gutiérrez**

> Están marcadas en **rojo** dentro de los `.docx` como "andamiaje" para completar.

### Formato y formalidades
- [ ] **Exportar el EFT a PDF** (Word → Guardar como → PDF). El EP3 acepta Word o PDF.
- [ ] Revisar que la portada/autores estén correctos en cada documento.
- [ ] Verificar norma APA en las referencias.

### Defensa (oral, individual, 10 min)
- [ ] Instalar dependencias y probar la **demo del agente en vivo**
      (`pip install -r requirements.txt` + `GITHUB_TOKEN`).
- [ ] Ensayar la presentación con el guion (`GUION_PRESENTACION_EFT.docx`).
- [ ] Preparar el dashboard para mostrarlo en la demo.

### Envío
- [ ] Subir informe(s) **PDF** + enlace al repositorio por **AVA**.
- [ ] Enviar copia al **correo del docente**.
- [ ] Confirmar el plazo del cronograma.

---

## ▶ Cómo reproducir todo (para el evaluador)

```bash
pip install -r requirements.txt
python run_observability.py        # pipeline completo
python -m pytest tests/ -v         # 22 pruebas
```

O ejecutar `entrega/evidencia/generar_evidencia.bat` (doble clic en Windows).
