import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundaryClass extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }
  
  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.reload();
  };
  
  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle={this.state.error?.message}
          extra={[
            <Button type="primary" key="reset" onClick={this.handleReset}>
              Reload Page
            </Button>,
          ]}
        />
      );
    }
    
    return this.props.children;
  }
}

export const ErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  return <ErrorBoundaryClass>{children}</ErrorBoundaryClass>;
};
