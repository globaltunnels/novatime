import React from 'react';
import { clsx } from 'clsx';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export interface TimerCardProps {
  isRunning?: boolean;
  project?: {
    id: string;
    name: string;
    color?: string;
  };
  task?: {
    id: string;
    title: string;
  };
  description?: string;
  elapsed?: string;
  onStart?: () => void;
  onStop?: () => void;
  onPause?: () => void;
  onEdit?: () => void;
}

export const TimerCard: React.FC<TimerCardProps> = ({
  isRunning = false,
  project,
  task,
  description,
  elapsed = '00:00:00',
  onStart,
  onStop,
  onPause,
  onEdit
}) => {
  return (
    <Card className={clsx(
      'transition-all duration-200',
      isRunning && 'ring-2 ring-[var(--time-active)] shadow-md'
    )}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            {/* Project and Task */}
            <div className="flex items-center gap-2 mb-2">
              {project && (
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: project.color || 'var(--primary)' }}
                  />
                  <span className="text-sm font-medium text-[var(--text)] truncate">
                    {project.name}
                  </span>
                </div>
              )}
              {task && (
                <>
                  <span className="text-[var(--text-muted)]">•</span>
                  <span className="text-sm text-[var(--text-muted)] truncate">
                    {task.title}
                  </span>
                </>
              )}
            </div>
            
            {/* Description */}
            {description && (
              <p className="text-sm text-[var(--text-muted)] mb-3 line-clamp-2">
                {description}
              </p>
            )}
            
            {/* Timer Display */}
            <div className="flex items-center gap-3">
              <div className="font-mono text-2xl font-bold text-[var(--text)]">
                {elapsed}
              </div>
              <Badge variant={isRunning ? 'success' : 'default'}>
                {isRunning ? 'Running' : 'Stopped'}
              </Badge>
            </div>
          </div>
          
          {/* Timer Controls */}
          <div className="flex items-center gap-2 ml-4">
            {!isRunning ? (
              <Button
                variant="primary"
                size="sm"
                onClick={onStart}
                className="bg-[var(--time-active)] hover:bg-green-600"
              >
                Start
              </Button>
            ) : (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={onPause}
                >
                  Pause
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={onStop}
                >
                  Stop
                </Button>
              </>
            )}
            {onEdit && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onEdit}
              >
                Edit
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};