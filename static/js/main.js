   // Utilidades UI
    const loader = document.getElementById('loader');
    const alertBox = document.getElementById('alertBox');
    const alertForm = document.getElementById('alertForm');

    function toggleLoader(show) {
      if (!loader) return;
      loader.classList.toggle('d-none', !show);
      loader.classList.toggle('d-flex', show);
    }
    function showAlert(el, type, msg) {
      el.className = 'alert alert-' + type;
      el.textContent = msg;
      el.classList.remove('d-none');
    }
    function hideAlert(el) { el.classList.add('d-none'); }

    // Botones de panel
    const btnOracle = document.getElementById('btnOracle');
    const btnMySQL = document.getElementById('btnMySQL');
    const btnSyncBoth = document.getElementById('btnSyncBoth');


    btnOracle?.addEventListener('click', async () => {
      hideAlert(alertBox); toggleLoader(true);
      try { const r = await fetch('/test_oracle'); const j = await r.json();
        showAlert(alertBox, 'primary', j.message || 'OK');
      } catch (e) { showAlert(alertBox, 'danger', 'Error: ' + e); }
      finally { toggleLoader(false); }
    });

    btnMySQL?.addEventListener('click', async () => {
      hideAlert(alertBox); toggleLoader(true);
      try { const r = await fetch('/test_mysql'); const j = await r.json();
        showAlert(alertBox, 'success', j.message || 'OK');
      } catch (e) { showAlert(alertBox, 'danger', 'Error: ' + e); }
      finally { toggleLoader(false); }
    });

    btnSyncBoth?.addEventListener('click', async () => {
      hideAlert(alertBox); toggleLoader(true);
      try { const r = await fetch('/sync_both'); const j = await r.json();
        if (j.ok) showAlert(alertBox, 'warning', `Sync OK → MySQL→Oracle (upserted: ${j.mysql_to_oracle.upserted}), Oracle→MySQL (upserted: ${j.oracle_to_mysql.upserted})`);
        else showAlert(alertBox, 'danger', 'Error: ' + (j.error || 'desconocido'));
      } catch (e) { showAlert(alertBox, 'danger', 'Error: ' + e); }
      finally { toggleLoader(false); }
    });



    // -------- Formulario PERSONA --------
    const personaInput = document.getElementById('PERSONA');
    const btnSaveOracle = document.getElementById('btnSaveOracle');
    const btnSaveMySQL  = document.getElementById('btnSaveMySQL');

    function buildPayload() {
      return {
        DPI: document.getElementById('DPI').value || null,
        PRIMER_NOMBRE: document.getElementById('PRIMER_NOMBRE').value || null,
        SEGUNDO_NOMBRE: document.getElementById('SEGUNDO_NOMBRE').value || null,
        PRIMER_APELLIDO: document.getElementById('PRIMER_APELLIDO').value || null,
        SEGUNDO_APELLIDO: document.getElementById('SEGUNDO_APELLIDO').value || null,
        DIRECCION: document.getElementById('DIRECCION').value || null,
        TELEFONO_CASA: document.getElementById('TELEFONO_CASA').value || null,
        TELEFONO_MOVIL: document.getElementById('TELEFONO_MOVIL').value || null,
        SALARIO_BASE: document.getElementById('SALARIO_BASE').value || null,
        BONIFICACION: document.getElementById('BONIFICACION').value || null,
      };
    }

    async function saveTo(url, dbName) {
      hideAlert(alertForm);
      try {
        const r = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildPayload())
        });
        const j = await r.json();
        if (!r.ok || !j.ok) {
          showAlert(alertForm, 'danger', j?.message || j?.error || `Error desconocido al insertar en ${dbName}`);
          return;
        }
        if (personaInput) personaInput.value = String(j.persona_id || '');
        showAlert(alertForm, 'success', `✔ Registro ingresado con EXITO en ${dbName.toUpperCase()}. Codigo: ${j.persona_id}`);

        // Limpieza
        ['DPI','PRIMER_NOMBRE','SEGUNDO_NOMBRE','PRIMER_APELLIDO','SEGUNDO_APELLIDO','DIRECCION','TELEFONO_CASA','TELEFONO_MOVIL','SALARIO_BASE','BONIFICACION']
          .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
      } catch (e) {
        showAlert(alertForm, 'danger', 'Error: ' + e);
      }
    }

    btnSaveOracle.addEventListener('click', () => saveTo('/oracle/personas', 'oracle'));
    btnSaveMySQL .addEventListener('click', () => saveTo('/mysql/personas',  'mysql'));

    // -------- Modal de eliminación --------
    const deleteModalEl = document.getElementById('deleteModal');
    const deleteModal = new bootstrap.Modal(deleteModalEl);
    const deleteModalTitle = document.getElementById('deleteModalTitle');
    const deletePersonaId = document.getElementById('deletePersonaId');
    const deleteError = document.getElementById('deleteError');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

    const btnDeleteOracle = document.getElementById('btnDeleteOracle');
    const btnDeleteMySQL  = document.getElementById('btnDeleteMySQL');

    let deleteTarget = 'oracle'; // 'oracle' | 'mysql'

    function openDeleteModal(target) {
      deleteTarget = target;
      deleteModalTitle.textContent = target === 'oracle' ? 'Eliminar en Oracle' : 'Eliminar en MySQL';

      // Prefill con el valor actual si es válido con prefijo
      const cur = (personaInput?.value || '').trim();
      deletePersonaId.value = /^(OR|MY)-\d{5}$/.test(cur) ? cur : '';
      deleteError.classList.add('d-none');

      deleteModal.show();
      setTimeout(() => deletePersonaId.focus(), 150);
    }

    btnDeleteOracle.addEventListener('click', () => openDeleteModal('oracle'));
    btnDeleteMySQL .addEventListener('click', () => openDeleteModal('mysql'));

    async function deleteFrom(url, dbName, id) {
      hideAlert(alertForm);
      try {
        const r = await fetch(`${url}/${encodeURIComponent(id)}`, { method: 'DELETE' });
        const j = await r.json();
        if (!r.ok || !j.ok) {
          showAlert(alertForm, 'danger', j?.message || j?.error || `Error al eliminar en ${dbName}`);
          return;
        }
        showAlert(alertForm, 'success', `🗑 ${dbName.toUpperCase()}: eliminadas ${j.deleted} fila(s) (PERSONA ${id}).`);
      } catch (e) {
        showAlert(alertForm, 'danger', 'Error: ' + e);
      }
    }

    confirmDeleteBtn.addEventListener('click', async () => {
      const raw = (deletePersonaId.value || '').trim().toUpperCase();

      // Acepta: OR-12345 | MY-12345 | 12345
      let id = null;
      if (/^(OR|MY)-\d{5}$/.test(raw)) {
        id = raw;
      } else if (/^\d{5}$/.test(raw)) {
        // Si solo puso 5 dígitos, anteponer prefijo según destino
        id = (deleteTarget === 'oracle' ? 'OR-' : 'MY-') + raw;
      }

      if (!id) {
        deleteError.classList.remove('d-none');
        deletePersonaId.focus();
        return;
      }
      deleteError.classList.add('d-none');

      const url = deleteTarget === 'oracle' ? '/oracle/personas' : '/mysql/personas';
      const name = deleteTarget;

      await deleteFrom(url, name, id);
      deleteModal.hide();
    });

    // Enter en el input de modal = confirmar
    deletePersonaId.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        confirmDeleteBtn.click();
      }
    });
