'use client'

export default function TutorialsPage() {
  const testAlert = () => {
    alert('BUTTON WORKS!')
  }

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">DEBUG TEST PAGE</h1>
      
      {/* Test if ANY button works */}
      <button 
        onClick={testAlert}
        className="bg-red-500 text-white px-6 py-3 rounded mb-4 block"
      >
        TEST BUTTON 1 - CLICK ME
      </button>

      <button 
        onClick={() => alert('Button 2 works!')}
        style={{ backgroundColor: 'blue', color: 'white', padding: '12px 24px', margin: '8px' }}
      >
        TEST BUTTON 2 - DIFFERENT STYLING
      </button>

      <div 
        onClick={() => alert('Div click works!')}
        className="bg-green-500 text-white p-4 cursor-pointer mb-4 inline-block"
      >
        CLICKABLE DIV
      </div>

      <a 
        href="https://youtube.com" 
        target="_blank" 
        className="bg-purple-500 text-white px-4 py-2 rounded inline-block"
      >
        LINK TO YOUTUBE
      </a>

      <p className="mt-8 text-lg">
        If you can click any of these elements, then our page structure works.
        If NONE of them work, there's a CSS or layout issue blocking clicks.
      </p>
    </div>
  )
}
