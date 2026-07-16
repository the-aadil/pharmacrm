import CRMForm from './CRMForm';
import ChatPanel from './ChatPanel';

export default function CRMPage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans" style={{ background: '#f0f2f5' }}>
      <div className="flex flex-1 w-full h-full">

        {/* LEFT FORM PANE
            p-8  → 32px padding on all sides
            overflow-y-auto + h-full → scrolls independently once content is taller than viewport
        */}
        <main
          className="flex-1 h-full overflow-y-auto bg-white border-r border-[#e5e7eb] p-8"
          style={{ minWidth: 0, scrollbarWidth: 'thin', scrollbarColor: '#cbd5e1 transparent' }}
        >
          <CRMForm />
        </main>

        {/* RIGHT AI PANEL
            p-6  → 24px padding on all sides
            overflow-y-auto + h-full → scrolls independently
        */}
        <aside
          className="w-[390px] min-w-[360px] max-w-[420px] h-full overflow-y-auto bg-white border-l border-[#e5e7eb] p-6"
          style={{ boxShadow: '-2px 0 8px rgba(0,0,0,0.04)', scrollbarWidth: 'thin', scrollbarColor: '#cbd5e1 transparent' }}
        >
          <ChatPanel />
        </aside>

      </div>
    </div>
  );
}
