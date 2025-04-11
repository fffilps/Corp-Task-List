import { useState } from 'react';

interface TaskExpiryProps {
  taskId: string;
  currentExpiry?: string;
  onSetExpiry: (taskId: string, hours: number) => Promise<void>;
}

export default function TaskExpiry({ taskId, currentExpiry, onSetExpiry }: TaskExpiryProps) {
  const [expiryHours, setExpiryHours] = useState<number>(24);
  const [isSetting, setIsSetting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSetExpiry = async () => {
    try {
      setIsSetting(true);
      setError(null);
      await onSetExpiry(taskId, expiryHours);
    } catch (error) {
      setError('Failed to set expiry time');
      console.error('Failed to set expiry:', error);
    } finally {
      setIsSetting(false);
    }
  };

  return (
    <div className="flex items-center space-x-4">
      {currentExpiry && (
        <span className="text-sm text-red-600">
          Expires: {new Date(currentExpiry).toLocaleString()}
        </span>
      )}
      {error && (
        <span className="text-sm text-red-600">{error}</span>
      )}
      <div className="flex items-center space-x-2">
        <input
          type="number"
          min="1"
          max="168"
          value={expiryHours}
          onChange={(e) => setExpiryHours(Number(e.target.value))}
          className="w-20 p-2 border-2 border-purple-900"
        />
        <button
          onClick={handleSetExpiry}
          disabled={isSetting}
          className="bg-purple-900 text-white px-4 py-2 hover:bg-pink-500 transition-all disabled:opacity-50"
        >
          {isSetting ? 'Setting...' : 'Set Expiry'}
        </button>
      </div>
    </div>
  );
} 