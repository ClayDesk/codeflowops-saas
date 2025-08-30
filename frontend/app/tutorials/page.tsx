'use client'

export default function TutorialsPage() {
  const testAlert = () => {
    alert('BUTTON WORKS!')
  }

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">DEBUG TEST PAGE - Updated {new Date().toISOString()}</h1>
      
      {/* Test if ANY button works */}
      <button 
        onClick={testAlert}
        className="bg-red-500 text-white px-6 py-3 rounded mb-4 block text-2xl"
      >
        🔴 TEST BUTTON 1 - CLICK ME 🔴
      </button>

      <button 
        onClick={() => alert('Button 2 works!')}
        style={{ backgroundColor: 'blue', color: 'white', padding: '20px 40px', margin: '16px', fontSize: '20px' }}
      >
        🔵 TEST BUTTON 2 - DIFFERENT STYLING 🔵
      </button>

      <div 
        onClick={() => alert('Div click works!')}
        className="bg-green-500 text-white p-6 cursor-pointer mb-4 inline-block text-xl"
      >
        🟢 CLICKABLE DIV 🟢
      </div>

      <a 
        href="https://youtube.com" 
        target="_blank" 
        className="bg-purple-500 text-white px-6 py-4 rounded inline-block text-xl"
      >
        🟣 LINK TO YOUTUBE 🟣
      </a>

      <p className="mt-8 text-lg bg-yellow-200 p-4">
        <strong>AMPLIFY CACHE BUSTER:</strong> If you can see this message and the colorful emoji buttons above, 
        the deployment worked! If you still see the old tutorials page, Amplify is caching.
      </p>

      <p className="mt-4 text-lg">
        If you can click any of these elements, then our page structure works.
        If NONE of them work, there's a CSS or layout issue blocking clicks.
      </p>
    </div>
  )
}
