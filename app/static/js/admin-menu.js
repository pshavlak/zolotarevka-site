/* ═══════════════════════════════════════════════════════════════════════════
   zolotarevka-site — Admin Menu Management
   ═══════════════════════════════════════════════════════════════════════════
   Requires: SortableJS (loaded in template)
   API base: /admin/menu
   ─────────────────────────────────────────────────────────────────────── */

const API_BASE = '/api/menu';

// ── State ──────────────────────────────────────────────────────────────────

let menuItems = [];

// ── DOM refs ───────────────────────────────────────────────────────────────

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const treeEl = document.getElementById('menu-tree');
const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const addBtn = document.getElementById('btn-add-item');
const itemFormModal = document.getElementById('item-form-modal');
const deleteModal = document.getElementById('delete-modal');
const itemForm = document.getElementById('item-form');
const modalTitle = document.getElementById('modal-title');

// ── Helpers ────────────────────────────────────────────────────────────────

function toast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => { el.remove(); }, 3000);
}

async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function openModal(modal) {
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(modal) {
  modal.classList.remove('active');
  document.body.style.overflow = '';
}

// ── Render Tree ────────────────────────────────────────────────────────────

function renderTree(items, level = 0) {
  return items.map((item, idx) => {
    const typeIcon = item.type === 'page' ? '📄' : item.type === 'header' ? '📋' : '🔗';
    const typeLabel = item.type === 'page' ? 'Страница' : item.type === 'header' ? 'Заголовок' : 'Ссылка';
    const typeTag = `tag-${item.type}`;
    const hasChildren = item.children && item.children.length > 0;
    const childrenHtml = hasChildren
      ? `<ul class="menu-tree">${renderTree(item.children, level + 1).join('')}</ul>`
      : '';

    return `
      <li class="menu-tree-item level-${Math.min(level, 3)}" data-id="${item.id}" data-parent="${item.parent_id || ''}" data-order="${item.order}">
        <div class="menu-item-row">
          <span class="drag-handle" data-sortable-handle>⠿</span>
          <div class="item-icon">${typeIcon}</div>
          <div class="item-info">
            <div class="item-title">${escHtml(item.title)}</div>
            <div class="item-meta">
              <span class="tag ${typeTag}">${typeLabel}</span>
              ${item.url ? `<span>${escHtml(truncateUrl(item.url))}</span>` : ''}
              ${item.is_active ? '' : '<span class="badge-inactive">Неактивен</span>'}
              <span>#${item.id}</span>
            </div>
          </div>
          <div class="item-actions">
            <button class="btn-icon" onclick="editItem(${item.id})" title="Редактировать">✏️</button>
            <button class="btn-icon danger" onclick="confirmDelete(${item.id})" title="Удалить">🗑️</button>
          </div>
        </div>
        ${childrenHtml}
      </li>
    `;
  }).join('');
}

function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function truncateUrl(url) {
  if (url.length <= 40) return url;
  return url.substring(0, 37) + '...';
}

function refreshTree() {
  loadingState.style.display = '';
  treeEl.innerHTML = '';
  emptyState.style.display = 'none';

  api('GET', '/tree')
    .then((data) => {
      menuItems = data;
      loadingState.style.display = 'none';
      if (data.length === 0) {
        emptyState.style.display = '';
        return;
      }
      treeEl.innerHTML = renderTree(data);
      initSortable();
    })
    .catch((err) => {
      loadingState.style.display = 'none';
      treeEl.innerHTML = `<div class="empty-state">
        <div class="icon">⚠️</div>
        <h3>Ошибка загрузки</h3>
        <p>${escHtml(err.message)}</p>
        <button class="btn btn-primary" onclick="refreshTree()">Повторить</button>
      </div>`;
    });
}

// ── SortableJS Init ────────────────────────────────────────────────────────

let sortableInstance = null;

function initSortable() {
  if (sortableInstance) sortableInstance.destroy();

  // Init on every nested <ul class="menu-tree"> so items can be moved
  // between different nesting levels.
  document.querySelectorAll('#menu-tree, #menu-tree .menu-tree').forEach((el) => {
    new Sortable(el, {
      group: 'menu-items',
      handle: '.drag-handle',
      animation: 200,
      easing: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      fallbackOnBody: true,
      swapThreshold: 0.5,
      onEnd: handleSortEnd,
    });
  });
}

function handleSortEnd(evt) {
  // Collect the new order from the DOM
  const reorderItems = [];
  const allItems = document.querySelectorAll('#menu-tree .menu-tree-item');

  allItems.forEach((item, idx) => {
    const parentLi = item.parentElement?.closest('.menu-tree-item');
    reorderItems.push({
      id: parseInt(item.dataset.id),
      parent_id: parentLi ? parseInt(parentLi.dataset.id) : null,
      order: idx,
    });
  });

  api('PUT', '/reorder', reorderItems)
    .then(() => toast('Порядок сохранён'))
    .catch((err) => {
      toast(`Ошибка: ${err.message}`, 'error');
      refreshTree(); // revert
    });
}

// ── Add / Edit Modal ──────────────────────────────────────────────────────

function buildParentOptions(selectedId) {
  let html = '<option value="">— Корневой элемент —</option>';
  function addOptions(items, prefix = '') {
    items.forEach((item) => {
      const isSelf = item.id === selectedId;
      const isChildOfSelected = isChildOf(item.id, selectedId);
      if (!isSelf && !isChildOfSelected) {
        html += `<option value="${item.id}" ${item.id === (selectedId || null) ? 'selected' : ''}>
          ${prefix}${escHtml(item.title)} (${item.type})</option>`;
      }
      if (item.children && item.children.length > 0) {
        addOptions(item.children, prefix + '— ');
      }
    });
  }
  addOptions(menuItems);
  return html;
}

function isChildOf(itemId, parentId) {
  if (!parentId) return false;
  // Walk up the tree to check
  function findParent(items, targetId) {
    for (const item of items) {
      if (item.id === targetId) return item;
      if (item.children) {
        const found = findParent(item.children, targetId);
        if (found) return found;
      }
    }
    return null;
  }
  const parent = findParent(menuItems, parentId);
  if (!parent || !parent.children) return false;
  return parent.children.some((c) => c.id === itemId);
}

function openItemForm(item) {
  const isEdit = !!item;
  modalTitle.textContent = isEdit ? 'Редактировать пункт меню' : 'Добавить пункт меню';

  document.getElementById('form-item-id').value = isEdit ? item.id : '';
  document.getElementById('form-title').value = isEdit ? item.title : '';
  document.getElementById('form-url').value = isEdit ? item.url : '';
  document.getElementById('form-type').value = isEdit ? item.type : 'page';
  document.getElementById('form-parent').innerHTML = buildParentOptions(isEdit ? item.parent_id : null);
  if (isEdit) document.getElementById('form-parent').value = item.parent_id || '';
  document.getElementById('form-active').checked = isEdit ? item.is_active : true;

  openModal(itemFormModal);
}

function closeItemForm() {
  closeModal(itemFormModal);
  itemForm.reset();
}

async function submitItemForm(e) {
  e.preventDefault();
  const itemId = document.getElementById('form-item-id').value;
  const data = {
    title: document.getElementById('form-title').value.trim(),
    url: document.getElementById('form-url').value.trim(),
    type: document.getElementById('form-type').value,
    parent_id: parseInt(document.getElementById('form-parent').value) || null,
    order: 0,
    is_active: document.getElementById('form-active').checked,
  };

  if (!data.title) {
    toast('Название обязательно', 'error');
    return;
  }

  try {
    if (itemId) {
      await api('PUT', `/items/${itemId}`, data);
      toast('Пункт обновлён');
    } else {
      await api('POST', '/items', data);
      toast('Пункт добавлен');
    }
    closeItemForm();
    refreshTree();
  } catch (err) {
    toast(`Ошибка: ${err.message}`, 'error');
  }
}

function editItem(id) {
  // Find item in tree
  function findInTree(items, targetId) {
    for (const item of items) {
      if (item.id === targetId) return item;
      if (item.children) {
        const found = findInTree(item.children, targetId);
        if (found) return found;
      }
    }
    return null;
  }
  const item = findInTree(menuItems, id);
  if (item) openItemForm(item);
}

// ── Delete ────────────────────────────────────────────────────────────────

let deleteTargetId = null;

function confirmDelete(id) {
  deleteTargetId = id;
  // Find item title
  function findTitle(items, targetId) {
    for (const item of items) {
      if (item.id === targetId) return item.title;
      if (item.children) {
        const found = findTitle(item.children, targetId);
        if (found) return found;
      }
    }
    return null;
  }
  const title = findTitle(menuItems, id) || `#${id}`;
  document.getElementById('delete-item-name').textContent = title;

  // Check for children
  function hasChildren(items, targetId) {
    for (const item of items) {
      if (item.id === targetId) return item.children && item.children.length > 0;
      if (item.children) {
        const found = hasChildren(item.children, targetId);
        if (found) return found;
      }
    }
    return false;
  }

  const warningEl = document.getElementById('delete-children-warning');
  if (hasChildren(menuItems, id)) {
    warningEl.style.display = '';
  } else {
    warningEl.style.display = 'none';
  }

  openModal(deleteModal);
}

async function executeDelete() {
  if (!deleteTargetId) return;
  try {
    await api('DELETE', `/items/${deleteTargetId}`);
    toast('Пункт удалён');
    closeModal(deleteModal);
    deleteTargetId = null;
    refreshTree();
  } catch (err) {
    toast(`Ошибка: ${err.message}`, 'error');
  }
}

function cancelDelete() {
  closeModal(deleteModal);
  deleteTargetId = null;
}

// ── Keyboard Shortcuts ────────────────────────────────────────────────────

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (itemFormModal.classList.contains('active')) closeItemForm();
    if (deleteModal.classList.contains('active')) cancelDelete();
  }
});

// Click outside modal to close
document.querySelectorAll('.modal-overlay').forEach((overlay) => {
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
});

// ── Init ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  refreshTree();
});
