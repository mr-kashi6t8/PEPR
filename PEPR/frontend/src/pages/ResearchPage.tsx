import React, { useState } from 'react';
import { Search, Download, Upload, FileText, X, CheckCircle2, Video, Newspaper, ExternalLink, AlertCircle } from 'lucide-react';
import { useResearch, useIngestPDFMutation, useNewsArticles } from '../api/hooks';
import type { NewsArticleItem } from '../api/types';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const ResearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('ALL');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // PDF Upload Form State
  const [title, setTitle] = useState('');
  const [authors, setAuthors] = useState('');
  const [docIdentifier, setDocIdentifier] = useState('');
  const [docType, setDocType] = useState('Working Paper');
  const [originalUrl, setOriginalUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<'RESEARCH' | 'MEDIA'>('RESEARCH');

  const { data: papers = [], refetch } = useResearch(query, selectedTopic);
  const { data: newsData } = useNewsArticles();
  const articles: NewsArticleItem[] = Array.isArray(newsData) ? newsData : (newsData as any)?.articles || [];
  const uploadMutation = useIngestPDFMutation();

  const topics = ['ALL', 'Energy Policy', 'Circular Debt', 'Tax Reform', 'Fiscal Policy', 'Exports', 'Macroeconomics'];

  const filteredArticles = query
    ? articles.filter((a: NewsArticleItem) => a.title.toLowerCase().includes(query.toLowerCase()) || (a.content && a.content.toLowerCase().includes(query.toLowerCase())))
    : articles;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a valid PDF (.pdf) file');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !authors || !docIdentifier || !selectedFile) {
      alert('Please fill out all required fields and attach a PDF document.');
      return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('authors', authors);
    formData.append('document_identifier', docIdentifier);
    formData.append('document_type', docType);
    if (originalUrl) formData.append('original_url', originalUrl);
    formData.append('file', selectedFile);

    uploadMutation.mutate(formData, {
      onSuccess: (data) => {
        setUploadSuccess(`Successfully ingested paper [${data.document_identifier || docIdentifier}] into Vector DB!`);
        refetch();
        setTimeout(() => {
          setIsModalOpen(false);
          setUploadSuccess(null);
          // Reset form
          setTitle('');
          setAuthors('');
          setDocIdentifier('');
          setOriginalUrl('');
          setSelectedFile(null);
        }, 1800);
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Institutional Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-serif text-[#0B2545]">
            PIDE Knowledge Base & Media Intelligence (M5)
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time PostgreSQL indexed PIDE Research Papers, Economic News feeds, and YouTube Talkshow Transcripts.
          </p>
        </div>

        {/* Action Controls & Upload Button */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="gold"
            icon={<Upload className="w-4 h-4" />}
            onClick={() => setIsModalOpen(true)}
          >
            Upload PIDE Research PDF
          </Button>

          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder={activeTab === 'RESEARCH' ? 'Search PIDE papers...' : 'Search media & YouTube transcripts...'}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30"
            />
          </div>

          {activeTab === 'RESEARCH' && (
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              className="px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg font-medium text-slate-700"
            >
              {topics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center border-b border-slate-200 gap-6 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('RESEARCH')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'RESEARCH'
              ? 'border-[#005A36] text-[#005A36]'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>PIDE Research Papers ({papers.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('MEDIA')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'MEDIA'
              ? 'border-[#005A36] text-[#005A36]'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Video className="w-4 h-4 text-red-600" />
          <span>Live Media & YouTube Transcripts ({articles.length})</span>
        </button>
      </div>

      {/* Upload Notification Banner */}
      {uploadSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-800 text-xs font-semibold animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Tab Content 1: Research Papers Grid */}
      {activeTab === 'RESEARCH' && (
        <div className="space-y-4">
          {papers.map((paper) => (
            <Card key={paper.id} hoverable accentBorder>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-2 max-w-4xl">
                  <div className="flex items-center gap-3">
                    <Badge variant="gold">{paper.document_type}</Badge>
                    <span className="text-xs font-mono font-bold text-[#005A36]">{paper.document_identifier}</span>
                    <span className="text-xs text-slate-400">• Published: {paper.published_date}</span>
                  </div>

                  <h3 className="text-lg font-bold text-[#0B2545] font-serif">{paper.title}</h3>
                  <p className="text-xs font-medium text-slate-500">Authors: {paper.authors}</p>
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">{paper.abstract}</p>

                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {paper.topics?.map((top) => (
                      <span key={top} className="px-2 py-0.5 bg-emerald-50 text-[#005A36] rounded-full text-[10px] font-medium border border-emerald-100">
                        {top}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col gap-2 min-w-[140px]">
                  {paper.original_url && paper.original_url !== '#' ? (
                    <a href={paper.original_url} target="_blank" rel="noreferrer">
                      <Button size="sm" variant="primary" icon={<Download className="w-3.5 h-3.5" />} className="w-full">
                        PDF Document
                      </Button>
                    </a>
                  ) : (
                    <Button size="sm" variant="outline" icon={<FileText className="w-3.5 h-3.5" />} disabled className="w-full">
                      Indexed in RAG
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Tab Content 2: Live Media & YouTube Transcripts Grid */}
      {activeTab === 'MEDIA' && (
        <div className="space-y-4">
          {filteredArticles.length === 0 ? (
            <Card className="text-center py-12">
              <p className="text-sm font-semibold text-slate-500">No media articles or YouTube talkshows found in database.</p>
              <p className="text-xs text-slate-400 mt-1">Run live ingestion from the Admin Panel to fetch real-time YouTube talkshow transcripts.</p>
            </Card>
          ) : (
            filteredArticles.map((article: NewsArticleItem) => {
              const isYoutube = article.is_youtube || article.url?.includes('youtube') || article.url?.includes('youtu.be');
              return (
                <Card key={article.id} hoverable accentBorder>
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-2 max-w-4xl">
                      <div className="flex items-center gap-3">
                        {isYoutube ? (
                          <Badge variant="critical">
                            <span className="flex items-center gap-1">
                              <Video className="w-3 h-3 text-white" />
                              YouTube Talkshow
                            </span>
                          </Badge>
                        ) : (
                          <Badge variant="medium">
                            <span className="flex items-center gap-1">
                              <Newspaper className="w-3 h-3" />
                              Economic News
                            </span>
                          </Badge>
                        )}
                        <span className="text-xs text-slate-400">
                          Published: {article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Recent'}
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-[#0B2545] font-serif">{article.title}</h3>
                      {article.content && (
                        <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed font-mono bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          {article.content}
                        </p>
                      )}
                    </div>

                    <div className="flex flex-col gap-2 min-w-[150px]">
                      <a href={article.url} target="_blank" rel="noreferrer">
                        <Button size="sm" variant={isYoutube ? 'gold' : 'primary'} icon={<ExternalLink className="w-3.5 h-3.5" />} className="w-full">
                          {isYoutube ? 'Watch Video' : 'Read Article'}
                        </Button>
                      </a>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      )}

      {/* PDF Upload Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full p-6 space-y-5 border border-slate-100 relative">
            {/* Close Button */}
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Modal Title */}
            <div>
              <div className="flex items-center gap-2 text-[#005A36] font-bold text-xs uppercase tracking-wider">
                <Upload className="w-4 h-4" />
                <span>PIDE Document Ingestion</span>
              </div>
              <h2 className="text-xl font-bold font-serif text-[#0B2545] mt-1">
                Upload PIDE Research Paper PDF
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Parsed page-by-page using PyMuPDF, chunked semantically, and embedded into Qdrant Vector Store for RAG citations.
              </p>
            </div>

            {/* Upload Form */}
            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Document Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Macroeconomic Implications of Energy Subsidies"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Authors <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Nadeem ul Haque"
                    value={authors}
                    onChange={(e) => setAuthors(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30 font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Document Identifier <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. PIDE-WP-2024-120"
                    value={docIdentifier}
                    onChange={(e) => setDocIdentifier(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30 font-mono font-bold text-[#005A36]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Document Type
                  </label>
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30 font-medium"
                  >
                    <option value="Working Paper">Working Paper</option>
                    <option value="Policy Brief">Policy Brief</option>
                    <option value="Research Report">Research Report</option>
                    <option value="Special Edition">Special Edition</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Original URL (Optional)
                  </label>
                  <input
                    type="url"
                    placeholder="https://pide.org.pk/..."
                    value={originalUrl}
                    onChange={(e) => setOriginalUrl(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005A36]/30"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  PDF Document File (.pdf) <span className="text-red-500">*</span>
                </label>
                <div className="border-2 border-dashed border-slate-200 rounded-xl p-4 text-center hover:border-[#005A36] transition-colors cursor-pointer relative bg-slate-50/50">
                  <input
                    type="file"
                    accept=".pdf"
                    required
                    onChange={handleFileChange}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />
                  <div className="flex flex-col items-center gap-1.5">
                    <FileText className="w-8 h-8 text-[#005A36]" />
                    <span className="text-xs font-semibold text-slate-700">
                      {selectedFile ? selectedFile.name : 'Click or Drag PDF file here'}
                    </span>
                    <span className="text-[10px] text-slate-400">Supported format: Adobe PDF (.pdf)</span>
                  </div>
                </div>
              </div>

              {uploadMutation.isError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-xs font-medium">
                  <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                  <span>{(uploadMutation.error as any)?.message || 'Upload failed. Check format or identifier.'}</span>
                </div>
              )}

              {/* Form Actions */}
              <div className="pt-3 border-t border-slate-100 flex justify-end gap-3">
                <Button variant="outline" size="sm" type="button" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="gold"
                  size="sm"
                  type="submit"
                  isLoading={uploadMutation.isPending}
                  icon={<Upload className="w-3.5 h-3.5" />}
                >
                  Upload & Ingest PDF
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
