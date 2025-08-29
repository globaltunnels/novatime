import React from 'react';
import { clsx } from 'clsx';
import { Card, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';

export interface TaskCardProps {
  task: {
    id: string;
    title: string;
    description?: string;
    status: 'todo' | 'in_progress' | 'review' | 'done' | 'blocked';
    priority: 'critical' | 'high' | 'medium' | 'low' | 'none';
    estimatedHours?: number;
    assignee?: {
      id: string;
      name: string;
      avatar?: string;
    };
    dueDate?: Date;
    labels?: Array<{
      id: string;
      name: string;
      color: string;
    }>;
  };
  onTaskClick?: (taskId: string) => void;
  onStartTimer?: (taskId: string) => void;
  className?: string;
}

const statusConfig = {
  todo: { label: 'To Do', variant: 'default' as const },
  in_progress: { label: 'In Progress', variant: 'info' as const },
  review: { label: 'In Review', variant: 'warning' as const },
  done: { label: 'Done', variant: 'success' as const },
  blocked: { label: 'Blocked', variant: 'error' as const }
};

const priorityConfig = {
  critical: { variant: 'priority-high' as const },
  high: { variant: 'priority-high' as const },
  medium: { variant: 'priority-medium' as const },
  low: { variant: 'priority-low' as const },
  none: { variant: 'default' as const }
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onTaskClick,
  onStartTimer,
  className
}) => {
  const handleCardClick = () => {
    onTaskClick?.(task.id);
  };

  const handleStartTimer = (e: React.MouseEvent) => {
    e.stopPropagation();
    onStartTimer?.(task.id);
  };

  const isOverdue = task.dueDate && new Date() > task.dueDate;

  return (
    <Card
      className={clsx(
        'cursor-pointer transition-all duration-200 hover:shadow-md hover:translate-y-[-1px]',
        isOverdue && 'border-[var(--error)]',
        className
      )}
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        {/* Header with Status and Priority */}
        <div className="flex items-center justify-between mb-2">
          <Badge variant={statusConfig[task.status].variant}>
            {statusConfig[task.status].label}
          </Badge>
          {task.priority !== 'none' && (
            <Badge variant={priorityConfig[task.priority].variant}>
              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
            </Badge>
          )}
        </div>
        
        {/* Task Title */}
        <h3 className="font-semibold text-[var(--text)] mb-2 line-clamp-2">
          {task.title}
        </h3>
        
        {/* Task Description */}
        {task.description && (
          <p className="text-sm text-[var(--text-muted)] mb-3 line-clamp-2">
            {task.description}
          </p>
        )}
        
        {/* Labels */}
        {task.labels && task.labels.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {task.labels.map((label) => (
              <span
                key={label.id}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                style={{
                  backgroundColor: label.color + '20',
                  color: label.color
                }}
              >
                {label.name}
              </span>
            ))}
          </div>
        )}
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]">
          <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
            {task.estimatedHours && (
              <span>⏱️ {task.estimatedHours}h</span>
            )}
            {task.dueDate && (
              <span className={clsx(isOverdue && 'text-[var(--error)]')}>
                📅 {task.dueDate.toLocaleDateString()}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {task.assignee && (
              <div className="flex items-center gap-2">
                {task.assignee.avatar ? (
                  <img
                    src={task.assignee.avatar}
                    alt={task.assignee.name}
                    className="w-6 h-6 rounded-full"
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-[var(--primary)] flex items-center justify-center text-white text-xs font-medium">
                    {task.assignee.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <span className="text-xs text-[var(--text-muted)]">
                  {task.assignee.name}
                </span>
              </div>
            )}
            
            {onStartTimer && (
              <button
                onClick={handleStartTimer}
                className="p-1 rounded hover:bg-[var(--bg)] transition-colors"
                title="Start timer"
              >
                ▶️
              </button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};