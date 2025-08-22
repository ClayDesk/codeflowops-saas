import { CheckCircle } from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Connect Your Repository',
    description: 'Simply paste your GitHub repository URL. We support both public and private repositories.',
    details: [
      'Automatic project detection',
      'Support for React, Vue, Angular, and static sites',
      'Private repository access via GitHub integration',
    ],
  },
  {
    number: '02',
    title: 'Intelligent Analysis',
    description: 'Our AI analyzes your project structure and automatically configures the optimal build settings.',
    details: [
      'Framework detection (React, Next.js, Vite)',
      'Package manager detection (npm, yarn, pnpm)',
      'Build configuration optimization',
    ],
  },
  {
    number: '03',
    title: 'Configure AWS',
    description: 'Add your AWS credentials and let us handle the infrastructure setup automatically.',
    details: [
      'Secure credential handling',
      'Automatic S3 bucket creation',
      'CloudFront distribution setup',
    ],
  },
  {
    number: '04',
    title: 'Deploy & Monitor',
    description: 'Watch your deployment happen in real-time with detailed logs and progress tracking.',
    details: [
      'Real-time build logs',
      'Automatic SSL certificate',
      'Performance monitoring',
    ],
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-white dark:bg-gray-950 transition-colors">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-20">
          <span className="inline-block bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 text-blue-700 dark:text-blue-200 px-4 py-1 rounded-full text-base font-semibold mb-5 tracking-wide shadow-sm">How It Works</span>
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-white mb-6 leading-tight">A 4-Step Automated Workflow</h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            From repository to production in minutes. Our platform automates every step for you.
          </p>
        </div>
        <div className="relative">
          <div className="absolute left-6 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-200 to-purple-200 dark:from-blue-900 dark:to-purple-900 rounded-full opacity-60" style={{zIndex:0}} />
          <div className="space-y-16 pl-0 md:pl-20 relative z-10">
            {steps.map((step, idx) => (
              <div key={step.number} className="flex items-start gap-8 relative">
                <div className="flex flex-col items-center">
                  <div className="w-14 h-14 flex items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-purple-600 text-white text-2xl font-bold shadow-lg border-4 border-white dark:border-gray-950">
                    {step.number}
                  </div>
                  {idx < steps.length - 1 && (
                    <div className="w-1 h-16 bg-gradient-to-b from-blue-200 to-purple-200 dark:from-blue-900 dark:to-purple-900 rounded-full opacity-60" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{step.title}</h3>
                  <p className="text-gray-600 dark:text-gray-300 mb-2 text-lg">{step.description}</p>
                  <ul className="list-disc list-inside text-gray-500 dark:text-gray-400 text-base space-y-1">
                    {step.details.map((detail, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-green-500 mt-1" />
                        <span>{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
