import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  deleteAction,
  deleteCategory,
  deleteCommentTemplate,
  deleteSportTemplate,
} from '../../db/cleanup';
import {
  createAction,
  createCategory,
  createCommentTemplate,
  listCategoriesByTemplateWithActions,
  updateActionHasOutcome,
  updateActionName,
} from '../../db/repository';
import type { Action, Category, CommentTemplate } from '../../types';

export function TemplateDetailPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const id = Number(templateId);

  const [categories, setCategories] = useState<Category[]>([]);
  const [actions, setActions] = useState<Record<number, Action[]>>({});
  const [comments, setComments] = useState<Record<number, CommentTemplate[]>>({});
  const [categoryName, setCategoryName] = useState('');
  const [newAction, setNewAction] = useState<Record<number, string>>({});
  const [newComment, setNewComment] = useState<Record<number, string>>({});
  const [editingActionId, setEditingActionId] = useState<number | null>(null);
  const [editActionName, setEditActionName] = useState('');

  async function load() {
    const data = await listCategoriesByTemplateWithActions(id);
    setCategories(data.categories);
    setActions(data.actions);
    setComments(data.comments);
  }

  useEffect(() => {
    if (id) void load();
  }, [id]);

  async function addCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!categoryName.trim()) return;
    await createCategory(id, categoryName.trim(), categories.length);
    setCategoryName('');
    await load();
  }

  async function addAction(categoryId: number) {
    const name = newAction[categoryId]?.trim();
    if (!name) return;
    const existing = actions[categoryId] ?? [];
    await createAction(categoryId, name, true, existing.length, 'handling');
    setNewAction((prev) => ({ ...prev, [categoryId]: '' }));
    await load();
  }

  async function toggleOutcome(action: Action) {
    if (!action.id) return;
    await updateActionHasOutcome(action.id, !action.hasOutcome);
    await load();
  }

  function startEditAction(action: Action) {
    if (!action.id) return;
    setEditingActionId(action.id);
    setEditActionName(action.name);
  }

  async function saveActionName(action: Action) {
    if (!action.id) return;
    const name = editActionName.trim();
    if (!name) return;
    await updateActionName(action.id, name);
    setEditingActionId(null);
    await load();
  }

  function cancelEditAction() {
    setEditingActionId(null);
    setEditActionName('');
  }

  async function addComment(actionId: number) {
    const text = newComment[actionId]?.trim();
    if (!text) return;
    const existing = comments[actionId] ?? [];
    await createCommentTemplate(actionId, text, existing.length);
    setNewComment((prev) => ({ ...prev, [actionId]: '' }));
    await load();
  }

  async function deleteActionHandler(action: Action) {
    if (!action.id || !confirm(`Удалить действие «${action.name}»?`)) return;
    await deleteAction(action.id);
    await load();
  }

  async function deleteCategoryHandler(category: Category) {
    if (!category.id || !confirm(`Удалить категорию «${category.name}» и все её действия?`)) return;
    await deleteCategory(category.id);
    await load();
  }

  async function deleteCommentHandler(comment: CommentTemplate) {
    if (!comment.id || !confirm(`Удалить подсказку «${comment.text}»?`)) return;
    await deleteCommentTemplate(comment.id);
    await load();
  }

  async function deleteTemplate() {
    if (!confirm('Удалить весь шаблон со всеми категориями и действиями?')) return;
    try {
      await deleteSportTemplate(id);
      window.location.href = '/directories/templates';
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Не удалось удалить шаблон');
    }
  }

  return (
    <div>
      <p>
        <Link to="/directories/templates">← Шаблоны</Link>
      </p>
      <h1 className="page-title">Категории и действия</h1>

      <div className="card">
        <button type="button" className="btn btn-danger" onClick={() => void deleteTemplate()}>
          Удалить шаблон
        </button>
      </div>

      <div className="card">
        <form className="form-row" onSubmit={addCategory}>
          <input
            placeholder="Новая категория"
            value={categoryName}
            onChange={(e) => setCategoryName(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">
            Добавить категорию
          </button>
        </form>
      </div>

      {categories.map((cat) => (
        <div className="card" key={cat.id}>
          <div className="form-row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, border: 'none', padding: 0 }}>{cat.name}</h3>
            <button
              type="button"
              className="btn btn-danger"
              onClick={() => void deleteCategoryHandler(cat)}
            >
              Удалить категорию
            </button>
          </div>
          <div className="form-row">
            <input
              placeholder="Новое действие"
              value={newAction[cat.id!] ?? ''}
              onChange={(e) =>
                setNewAction((prev) => ({ ...prev, [cat.id!]: e.target.value }))
              }
            />
            <button type="button" className="btn" onClick={() => void addAction(cat.id!)}>
              Добавить действие
            </button>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Действие</th>
                <th>Результат</th>
                <th>Комментарии-подсказки</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(actions[cat.id!] ?? []).map((act) => (
                <tr key={act.id}>
                  <td>
                    {editingActionId === act.id ? (
                      <div className="form-row">
                        <input
                          value={editActionName}
                          onChange={(e) => setEditActionName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') void saveActionName(act);
                            if (e.key === 'Escape') cancelEditAction();
                          }}
                          autoFocus
                        />
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={() => void saveActionName(act)}
                        >
                          Сохранить
                        </button>
                        <button type="button" className="btn" onClick={cancelEditAction}>
                          Отмена
                        </button>
                      </div>
                    ) : (
                      <div className="form-row" style={{ alignItems: 'center' }}>
                        <span>{act.name}</span>
                        <button
                          type="button"
                          className="btn"
                          onClick={() => startEditAction(act)}
                        >
                          Изменить
                        </button>
                      </div>
                    )}
                  </td>
                  <td>
                    <button type="button" className="btn" onClick={() => void toggleOutcome(act)}>
                      {act.hasOutcome ? 'Да' : 'Нет'}
                    </button>
                  </td>
                  <td>
                    <div className="form-row">
                      {(comments[act.id!] ?? []).map((c) => (
                        <span
                          key={c.id}
                          className="muted"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                        >
                          {c.text}
                          <button
                            type="button"
                            className="btn btn-danger"
                            style={{ padding: '2px 6px', fontSize: 11 }}
                            onClick={() => void deleteCommentHandler(c)}
                          >
                            ✕
                          </button>
                        </span>
                      ))}
                    </div>
                    <div className="form-row">
                      <input
                        placeholder="Подсказка"
                        value={newComment[act.id!] ?? ''}
                        onChange={(e) =>
                          setNewComment((prev) => ({ ...prev, [act.id!]: e.target.value }))
                        }
                      />
                      <button
                        type="button"
                        className="btn"
                        onClick={() => void addComment(act.id!)}
                      >
                        +
                      </button>
                    </div>
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => void deleteActionHandler(act)}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
