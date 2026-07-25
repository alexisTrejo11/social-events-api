export interface ProjectDocsModel {
  codeShowcase: ProjectCodeShowCase;
  overview: ProjectOverview;
  infrastructure: InfrastructureModel;
  architecture: ProjectArchitectureModel;
  features: ProjectFeatures;
  apiSchema: APISchema;
}

// Section: Overview
export interface ProjectOverview {
  problemStatement: OverviewProblemStatement;
  solution: OverviewSolution;
  keyMetrics: OverviewKeyMetrics;
  links: ProjectLinks;
  mediaGallery: MediaGallerySection;
  mediaItems: ProjectMediaItem[];
  metrics: ProjectMetric[];
}

export interface ProjectMetric {
  label: string;
  value: string;
  description?: string;
}

export interface ProjectSection {
  id: string;
  title: string;
  content: string;
  subsections?: ProjectSection[];
}

export interface ProjectFilters {
  category?: string;
  status?: string;
  type?: string;
  technologies?: string[];
  year?: number;
  featured?: boolean;
  searchTerm?: string;
}

export interface ProjectLinks {
  github: string | null;
  demo: string | null;
  documentation: string | null;
  dockerHub: string | null;
}

export interface ProjectImages {
  cover: string | null;
  screenshots: string[];
  diagram: string | null;
}

export interface Technology {
  name: string;
  category: string;
  usage: string;
  iconPath?: string;
  icon?: string;
  version?: string;
}

export interface QuickLink {
  title: string;
  description: string;
  url: string;
  iconPath: string;
  color: string;
  external: boolean;
}

export interface ProjectMediaItem {
  type: 'image' | 'video';
  url: string;
  thumbnail?: string;
  title: string;
  description: string;
  alt?: string;
  category?: 'screenshot' | 'diagram' | 'demo' | 'architecture';
}

export interface MediaGallerySection {
  title: string;
  description?: string;
  items: ProjectMediaItem[];
}

export interface OverviewProblemStatement {
  problemTitle: string;
  problemDescription: string;
  problemList: string[];
}

export interface OverviewSolution {
  solutionTitle: string;
  solutionList: Solution[];
}

export interface Solution {
  title: string;
  description: string;
}

export interface OverviewKeyMetrics {
  metricsTitle: string;
  metricsList: string[];
}

export interface MediaItem {
  type: 'image' | 'video';
  url: string;
  thumbnail?: string;
  title: string;
  description: string;
  alt?: string;
}

// Section: Code Showcase
export interface ProjectCodeShowCase {
  codeExamples: CodeExample[];
}

export interface CodeShowcase {
  examples: CodeExample[];
}

export interface CodeExample {
  id: string;
  title: string;
  description: string;
  category: string;
  files: CodeFile[];
  duration?: string;
  views?: number;
  tags?: string[];
}

export interface CodeFile {
  name: string;
  path: string;
  language: string;
  content: string;
  highlighted?: boolean;
  explanation?: string;
}

// Section: Infrastructure
export interface InfrastructureModel {
  deploymentLayers: DeploymentLayer[];
  dockerFiles: DockerFile[];
  // TODO: Add In Existing Project Docs
  cloudServices: CloudService[];
  metrics: InfrastructureMetric[];
}

export interface InfrastructureMetric {
  label: string;
  value: string;
  icon: string;
  description: string;
}

export interface CloudService {
  name: string;
  purpose: string;
  icon: string;
  cost: string;
}

export interface DeploymentLayer {
  name: string;
  components: DeploymentComponent[];
  color: string;
}

export interface DeploymentComponent {
  name: string;
  icon: string;
  description: string;
}

export interface DockerFile {
  service: string;
  content: string;
  description: string;
}

export interface PipelineStage {
  name: string;
  steps: PipelineStep[];
  icon: string;
  duration: string;
}

export interface PipelineStep {
  name: string;
  description: string;
  status: 'success' | 'running' | 'pending';
}

// Section: Features
export interface ProjectFeatures {
  features: ProjectFeature[];
}

export interface ProjectFeature {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: FeatureCategory;
  status: FeatureStatus;
  highlights: string[];
  techStack?: string[];
  metrics?: FeatureMetric[];
  codeSnippet?: CodeSnippet;
}

export interface FeatureMetric {
  label: string;
  value: string;
  trend?: 'up' | 'down' | 'stable';
  icon?: string;
}

export interface CodeSnippet {
  language: string;
  code: string;
  filename?: string;
}

export type FeatureCategory =
  | 'authentication'
  | 'database'
  | 'api'
  | 'security'
  | 'performance'
  | 'integration'
  | 'messaging'
  | 'caching'
  | 'monitoring'
  | 'testing';

export type FeatureStatus = 'stable' | 'beta' | 'experimental' | 'deprecated';

// Section: Architecture
export interface ProjectArchitectureModel {
  layers: ArchitectureLayer[];
  designPatterns: DesignPattern[];
  scalabilityStrategies: StrategyItem[];
  securityStrategies: StrategyItem[];
  cacheStrategies: CacheStrategy[];
  architectureFeatures: ArchitectureFeature[];

  architectureDiagram: ArchitectureDiagramModel;
  dataFlow: DataFlowModel;
  techDecisions: TechDecisionsModel;
}

// Base Architecture Models
export interface ArchitectureLayer {
  name: string;
  description: string;
  components: string[];
  color: string;
  expanded?: boolean;
  responsibilities?: string[];
  technologies?: string[];
}

export interface DesignPattern {
  title: string;
  emoji: string;
  description: string;
  category: string;
  badge: string;
}

export interface StrategyItem {
  title: string;
  description: string;
}

export interface CacheStrategy {
  name: string;
  description: string;
  ttl: string;
  coverage: string;
}

export interface ArchitectureFeature {
  title: string;
  emoji: string;
  description: string;
}

export interface ArchitectureDiagramModel {
  legendItems: LegendItem[];
  nodes: DiagramNode[];
  connections: DiagramConnection[];
}

export interface DiagramNode {
  id: string;
  label: string;
  type: 'client' | 'gateway' | 'service' | 'database' | 'queue' | 'monitoring';
  x: number;
  y: number;
  connections?: string[];
  status?: 'healthy' | 'warning' | 'error';
  traffic?: number; // simulated traffic
}

export interface DiagramConnection {
  id: string;
  from: string;
  to: string;
  label?: string;
  protocol?: string;
  isActive?: boolean;
}

export interface LegendItem {
  type: string;
  label: string;
  color: string;
  icon: string;
}

export interface DataFlowModel {
  requestFlow: FlowStep[];
  eventFlow: FlowStep[];
}

export interface FlowStep {
  number: number;
  title: string;
  description: string;
  icon: string;
}

export interface TechDecisionsModel {
  decisions: TechDecisionModel[];
}

export interface TechDecisionModel {
  title: string;
  problem: string;
  solution: string;
  alternatives: string[];
  outcome: string;
  icon: string;
}

// Section: APIs
export interface APISchema {
  httpEndpoints: ApiEndpoint[];
  type: 'REST' | 'GraphQL' | 'SOAP' | 'Mixed';
}

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface ApiEndpoint {
  id: string;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  urlPath: string;
  summary: string;
  description: string;
  tags: string[];
  authenticated: boolean;
  rateLimit: string;
  parameters?: ApiParameter[];
  requestBody?: ApiRequestBody;
  responses: ApiResponse[];
}

export interface ApiParameter {
  name: string;
  in: 'path' | 'query' | 'header';
  type: string;
  required: boolean;
  description: string;
  example?: JsonValue;
}

export interface ApiRequestBody {
  contentType: string;
  schema: JsonValue;
  example: JsonValue;
}

export interface ApiResponse {
  status: number;
  description: string;
  schema?: JsonValue;
  example: JsonValue;
}
