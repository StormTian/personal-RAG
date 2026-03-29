"""OpenTelemetry tracing configuration for RAG system."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import Status, StatusCode

from rag_system.config.settings import get_settings

settings = get_settings()


def init_tracing(service_name: str = "rag-service", service_version: str = "1.0.0"):
    """Initialize OpenTelemetry tracing.
    
    Args:
        service_name: Name of the service for tracing
        service_version: Version of the service
        
    Returns:
        TracerProvider instance
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })
    
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure OTLP exporter if monitoring is enabled
    if settings.monitoring.enabled and settings.monitoring.otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.monitoring.otlp_endpoint,
                insecure=True,
            )
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception as e:
            print(f"Failed to configure OTLP exporter: {e}")
    
    # Always add console exporter for debugging
    console_exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    return provider


def get_tracer(name: str = "rag-service"):
    """Get tracer instance."""
    return trace.get_tracer(name)


def set_span_status(span, error: Exception = None):
    """Set span status based on error."""
    if error:
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
    else:
        span.set_status(Status(StatusCode.OK))
